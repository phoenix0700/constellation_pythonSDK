#!/usr/bin/env python3
"""
Constellation Network Python SDK - Command Line Interface

A comprehensive CLI tool for interacting with the Constellation Network.
Provides easy access to account management, balance queries, transactions,
network information, and metagraph operations.

Usage:
    constellation --help
    constellation account create
    constellation balance <address>
    constellation send <amount> <to_address> --from-key <private_key>
    constellation network info
    constellation metagraph discover --production
    constellation simulate dag <source> <destination> <amount>
    constellation simulate token <source> <destination> <amount> <metagraph_id>
    constellation simulate data <source> <metagraph_id> --data '{"key": "value"}'
    constellation simulate cost <source> <destination> <amount>
    constellation stream transactions --duration 60 --addresses <address>
    constellation stream balance <address> --duration 300
    constellation stream events --event-types transaction --duration 120
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict

try:
    import click
except ImportError:
    print("Error: 'click' library is required for CLI functionality.")
    print("Install it with: pip install click")
    sys.exit(1)

from .account import Account
from .batch import (
    BatchOperation,
    BatchOperationType,
    BatchResponse,
    BatchResult,
    batch_get_balances,
    batch_get_ordinals,
    batch_get_transactions,
    create_batch_operation,
)
from .exceptions import ConstellationError, NetworkError, ValidationError
from .metagraph import MetagraphClient
from .network import Network
from .simulation import (
    TransactionSimulator,
    estimate_transaction_cost,
    simulate_transaction,
)
from .transactions import Transactions
from .validation import AddressValidator

# Streaming imports (optional)
try:
    from .streaming import (
        BalanceTracker,
        EventFilter,
        EventType,
        NetworkEventStream,
        create_event_stream,
    )

    STREAMING_AVAILABLE = True
except ImportError:
    STREAMING_AVAILABLE = False

try:
    from .async_metagraph import discover_metagraphs_async
    from .metagraph import discover_production_metagraphs

    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False


# CLI Configuration
CLI_CONFIG_FILE = Path.home() / ".constellation" / "cli-config.json"
DEFAULT_NETWORK = "testnet"


class CLIConfig:
    """CLI-specific configuration management."""

    def __init__(self):
        self.config_file = CLI_CONFIG_FILE
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load CLI configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        return {
            "default_network": DEFAULT_NETWORK,
            "default_private_key": None,
            "output_format": "pretty",
            "async_enabled": ASYNC_AVAILABLE,
        }

    def save_config(self):
        """Save CLI configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)

    def get(self, key: str, default=None):
        """Get configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value."""
        self.config[key] = value
        self.save_config()


# Global CLI config instance
cli_config = CLIConfig()


def format_output(data: Any, format_type: str = None) -> str:
    """Format output based on specified format."""
    format_type = format_type or cli_config.get("output_format", "pretty")

    if format_type == "json":
        return json.dumps(data, indent=2)
    elif format_type == "pretty":
        if isinstance(data, dict):
            output = []
            for key, value in data.items():
                if isinstance(value, dict):
                    output.append(f"{key}:")
                    for k, v in value.items():
                        output.append(f"  {k}: {v}")
                else:
                    output.append(f"{key}: {value}")
            return "\n".join(output)
        else:
            return str(data)
    else:
        return str(data)


def handle_errors(func):
    """Decorator to handle common CLI errors."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            click.echo(f"❌ Validation Error: {e}", err=True)
            sys.exit(1)
        except NetworkError as e:
            click.echo(f"❌ Network Error: {e}", err=True)
            sys.exit(1)
        except ConstellationError as e:
            click.echo(f"❌ Constellation Error: {e}", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Unexpected Error: {e}", err=True)
            sys.exit(1)

    return wrapper


@click.group()
@click.option(
    "--network",
    "-n",
    default=None,
    help="Network to use (mainnet, testnet, integrationnet)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["pretty", "json"]),
    default=None,
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, network, output, verbose):
    """Constellation Network Python SDK CLI

    Interact with the Constellation Network from the command line.
    """
    ctx.ensure_object(dict)

    # Set network
    ctx.obj["network"] = network or cli_config.get("default_network", DEFAULT_NETWORK)

    # Set output format
    if output:
        ctx.obj["output_format"] = output
    else:
        ctx.obj["output_format"] = cli_config.get("output_format", "pretty")

    ctx.obj["verbose"] = verbose

    # Configure SDK for selected network
    try:
        from .config import DEFAULT_CONFIGS

        if ctx.obj["network"] not in DEFAULT_CONFIGS:
            click.echo(f"❌ Unknown network: {ctx.obj['network']}", err=True)
            sys.exit(1)
    except Exception as e:
        if verbose:
            click.echo(f"⚠️  Configuration warning: {e}", err=True)


# Account Management Commands
@cli.group()
def account():
    """Account management commands."""
    pass


@account.command("create")
@click.option("--save-key", is_flag=True, help="Save private key to CLI config")
@click.pass_context
@handle_errors
def create_account(ctx, save_key):
    """Create a new Constellation account."""
    acc = Account()

    output = {
        "address": acc.address,
        "public_key": acc.public_key_hex,
        "private_key": acc.private_key_hex if save_key else "***HIDDEN***",
    }

    if save_key:
        cli_config.set("default_private_key", acc.private_key_hex)
        click.echo("🔐 Private key saved to CLI config")

    click.echo("✅ New account created:")
    click.echo(format_output(output, ctx.obj["output_format"]))

    if not save_key:
        click.echo(f"\n🔑 Private Key (save this!): {acc.private_key_hex}")


@account.command("info")
@click.argument("address", required=False)
@click.pass_context
@handle_errors
def account_info(ctx, address):
    """Get account information."""
    if not address:
        # Try to use default private key to get address
        private_key = cli_config.get("default_private_key")
        if not private_key:
            click.echo(
                "❌ No address provided and no default private key configured", err=True
            )
            sys.exit(1)

        acc = Account(private_key)
        address = acc.address

    network = Network(ctx.obj["network"])

    try:
        balance_info = network.get_balance(address)

        # Handle both dict and int responses from get_balance
        if isinstance(balance_info, dict):
            balance = balance_info.get("balance", "N/A")
            ordinal = balance_info.get("ordinal", "N/A")
        else:
            # If it's just an integer balance
            balance = balance_info
            ordinal = "N/A"

        output = {
            "address": address,
            "balance": balance,
            "ordinal": ordinal,
        }

        click.echo(format_output(output, ctx.obj["output_format"]))
    except Exception as e:
        click.echo(f"❌ Could not retrieve account info: {e}", err=True)


# Balance Commands
@cli.command("balance")
@click.argument("address")
@click.option(
    "--watch", "-w", is_flag=True, help="Watch balance changes (refresh every 30s)"
)
@click.pass_context
@handle_errors
def get_balance(ctx, address, watch):
    """Get DAG balance for an address."""
    network = Network(ctx.obj["network"])

    def fetch_balance():
        balance_info = network.get_balance(address)

        # Handle both dict and int responses from get_balance
        if isinstance(balance_info, dict):
            balance = balance_info.get("balance", "0")
            ordinal = balance_info.get("ordinal", 0)
        else:
            # If it's just an integer balance
            balance = balance_info
            ordinal = 0

        output = {
            "address": address,
            "balance": balance,
            "ordinal": ordinal,
            "network": ctx.obj["network"],
        }
        return output

    if watch:
        click.echo(f"👀 Watching balance for {address} (Ctrl+C to stop)\n")
        try:
            while True:
                output = fetch_balance()
                click.clear()
                from datetime import datetime

                click.echo(
                    f"🔄 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                click.echo(format_output(output, ctx.obj["output_format"]))
                click.echo("\nPress Ctrl+C to stop watching...")

                import time

                time.sleep(30)
        except KeyboardInterrupt:
            click.echo("\n👋 Stopped watching balance")
    else:
        output = fetch_balance()
        click.echo(format_output(output, ctx.obj["output_format"]))


# Transaction Commands
@cli.command("send")
@click.argument("amount", type=float)
@click.argument("to_address")
@click.option("--from-key", help="Private key to send from")
@click.option("--fee", type=float, default=0, help="Transaction fee (default: 0)")
@click.option("--dry-run", is_flag=True, help="Create transaction but do not submit")
@click.pass_context
@handle_errors
def send_transaction(ctx, amount, to_address, from_key, fee, dry_run):
    """Send DAG tokens to an address."""
    # Get private key
    private_key_hex = from_key or cli_config.get("default_private_key")
    if not private_key_hex:
        click.echo(
            "❌ No private key provided. Use --from-key or configure default key",
            err=True,
        )
        sys.exit(1)

    # Create account
    acc = Account(private_key_hex)

    # Create network client
    network = Network(ctx.obj["network"])

    # Get current balance and ordinal
    balance_info = network.get_balance(acc.address)

    # Handle both dict and int responses from get_balance
    if isinstance(balance_info, dict):
        current_balance = float(balance_info.get("balance", 0))
        last_ref_hash = balance_info.get("lastTransactionRef", {}).get("hash", "")
    else:
        # If it's just an integer balance
        current_balance = float(balance_info)
        last_ref_hash = ""

    if amount > current_balance:
        click.echo(
            f"❌ Insufficient balance. Available: {current_balance}, Requested: {amount}",
            err=True,
        )
        sys.exit(1)

    # Create transaction
    from constellation_sdk.transactions import create_dag_transaction

    tx_data = create_dag_transaction(
        sender=acc,
        destination=to_address,
        amount=amount,
        fee=fee,
        parent=last_ref_hash,
    )

    if dry_run:
        click.echo("🔍 Dry run - transaction created but not submitted:")
        click.echo(format_output(tx_data, ctx.obj["output_format"]))
        return

    # Submit transaction
    result = network.submit_transaction(tx_data)

    output = {
        "transaction_hash": result.get("hash", "N/A"),
        "from": acc.address,
        "to": to_address,
        "amount": amount,
        "fee": fee,
        "status": "submitted",
        "network": ctx.obj["network"],
    }

    click.echo("✅ Transaction submitted successfully:")
    click.echo(format_output(output, ctx.obj["output_format"]))


# Network Commands
@cli.group()
def network():
    """Network information and operations."""
    pass


@network.command("info")
@click.pass_context
@handle_errors
def network_info(ctx):
    """Get network information."""
    net = Network(ctx.obj["network"])

    try:
        node_info = net.get_node_info()
        cluster_info = net.get_cluster_info()

        output = {
            "network": ctx.obj["network"],
            "node_info": {
                "id": node_info.get("id", "N/A"),
                "version": node_info.get("version", "N/A"),
                "state": node_info.get("state", "N/A"),
            },
            "cluster_info": {
                "node_count": len(cluster_info) if cluster_info else 0,
                "nodes": cluster_info[:3] if cluster_info else [],  # Show first 3 nodes
            },
        }

        click.echo(format_output(output, ctx.obj["output_format"]))
    except Exception as e:
        click.echo(f"❌ Could not retrieve network info: {e}", err=True)


@network.command("health")
@click.pass_context
@handle_errors
def network_health(ctx):
    """Check network health."""
    net = Network(ctx.obj["network"])

    try:
        # Try to get node info
        node_info = net.get_node_info()
        healthy = True
        status = "healthy"
    except Exception as e:
        healthy = False
        status = f"unhealthy: {e}"

    output = {"network": ctx.obj["network"], "healthy": healthy, "status": status}

    if healthy:
        click.echo("✅ Network is healthy")
    else:
        click.echo("❌ Network health check failed")

    if ctx.obj["verbose"]:
        click.echo(format_output(output, ctx.obj["output_format"]))


# Metagraph Commands
@cli.group()
def metagraph():
    """Metagraph discovery and operations."""
    pass


@metagraph.command("discover")
@click.option("--production", is_flag=True, help="Only show production metagraphs")
@click.option("--async", "use_async", is_flag=True, help="Use async discovery (faster)")
@click.pass_context
@handle_errors
def discover_metagraphs(ctx, production, use_async):
    """Discover available metagraphs."""

    def sync_discover():
        if production:
            return discover_production_metagraphs()
        else:
            client = MetagraphClient(ctx.obj["network"])
            return client.discover_metagraphs()

    async def async_discover():
        if ASYNC_AVAILABLE and use_async:
            # Get all metagraphs first, then filter if needed
            metagraphs = await discover_metagraphs_async()
            if production and metagraphs:
                # Filter for production metagraphs
                return [mg for mg in metagraphs if mg.get("category") == "production"]
            return metagraphs
        else:
            return sync_discover()

    if use_async and not ASYNC_AVAILABLE:
        click.echo("⚠️  Async not available, using sync discovery", err=True)
        use_async = False

    if use_async:
        metagraphs = asyncio.run(async_discover())
    else:
        metagraphs = sync_discover()

    if not metagraphs:
        click.echo("❌ No metagraphs found")
        return

    output = {
        "count": len(metagraphs),
        "metagraphs": metagraphs,
        "network": ctx.obj["network"],
        "production_only": production,
    }

    click.echo(f"✅ Found {len(metagraphs)} metagraph(s):")
    click.echo(format_output(output, ctx.obj["output_format"]))


# Configuration Commands
@cli.group()
def config():
    """CLI configuration management."""
    pass


@config.command("show")
@click.pass_context
def show_config(ctx):
    """Show current CLI configuration."""
    output = {
        "cli_config_file": str(cli_config.config_file),
        "cli_settings": cli_config.config,
        "current_network": ctx.obj["network"],
        "output_format": ctx.obj["output_format"],
        "async_available": ASYNC_AVAILABLE,
    }

    click.echo(format_output(output, ctx.obj["output_format"]))


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_config_value(key, value):
    """Set a configuration value."""
    # Try to parse as JSON for complex values
    try:
        value = json.loads(value)
    except:
        pass  # Keep as string

    cli_config.set(key, value)
    click.echo(f"✅ Set {key} = {value}")


@config.command("reset")
@click.confirmation_option(prompt="Reset all CLI configuration?")
def reset_config():
    """Reset CLI configuration to defaults."""
    global cli_config
    if cli_config.config_file.exists():
        cli_config.config_file.unlink()

    cli_config = CLIConfig()  # Reinitialize with defaults
    click.echo("✅ CLI configuration reset to defaults")


# =====================
# Simulation Commands
# =====================


@cli.group()
def simulate():
    """Transaction simulation and validation commands."""
    pass


@simulate.command("dag")
@click.argument("source")
@click.argument("destination")
@click.argument("amount", type=float)
@click.option("--fee", type=float, default=0, help="Transaction fee (default: 0)")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed analysis")
@click.option("--no-balance-check", is_flag=True, help="Skip balance check")
@click.pass_context
@handle_errors
def simulate_dag(ctx, source, destination, amount, fee, detailed, no_balance_check):
    """Simulate a DAG transfer transaction."""
    net = Network(ctx.obj["network"])

    try:
        # Validate addresses
        if not AddressValidator.validate_format(source):
            click.echo(f"❌ Invalid source address: {source}", err=True)
            return
        if not AddressValidator.validate_format(destination):
            click.echo(f"❌ Invalid destination address: {destination}", err=True)
            return

        # Convert amount to nanograms
        amount_ng = int(amount * 1e8)
        fee_ng = int(fee * 1e8)

        # Run simulation
        simulation = Transactions.simulate_dag_transfer(
            source=source,
            destination=destination,
            amount=amount_ng,
            network=net,
            fee=fee_ng,
            check_balance=not no_balance_check,
            detailed_analysis=detailed,
        )

        # Display results
        click.echo(f"🔮 DAG Transfer Simulation")
        click.echo(f"{'='*40}")
        click.echo(f"Source: {source}")
        click.echo(f"Destination: {destination}")
        click.echo(f"Amount: {amount} DAG")
        if fee > 0:
            click.echo(f"Fee: {fee} DAG")
        click.echo()

        # Success status
        if simulation["will_succeed"]:
            click.echo("✅ Transaction will succeed")
        else:
            click.echo("❌ Transaction will fail")

        click.echo(f"Success Probability: {simulation['success_probability']:.1%}")
        click.echo(f"Estimated Size: {simulation['estimated_size']} bytes")

        if not no_balance_check:
            if simulation["balance_sufficient"]:
                click.echo("✅ Balance is sufficient")
            else:
                click.echo("❌ Insufficient balance")
                if "source_balance" in simulation:
                    current_balance = simulation["source_balance"] / 1e8
                    needed = simulation["total_needed"] / 1e8
                    click.echo(f"   Current: {current_balance} DAG")
                    click.echo(f"   Needed: {needed} DAG")

        # Validation errors
        if simulation["validation_errors"]:
            click.echo("\n❌ Validation Errors:")
            for error in simulation["validation_errors"]:
                click.echo(f"   • {error}")

        # Warnings
        if simulation["warnings"]:
            click.echo("\n⚠️  Warnings:")
            for warning in simulation["warnings"]:
                click.echo(f"   • {warning}")

        # Detailed analysis
        if detailed and "detailed_analysis" in simulation:
            analysis = simulation["detailed_analysis"]
            click.echo(f"\n📊 Detailed Analysis:")
            click.echo(f"   Complexity: {analysis['transaction_complexity']}")
            click.echo(f"   Processing Time: {analysis['estimated_processing_time']}")
            click.echo(
                f"   Network Requirements: {', '.join(analysis['network_requirements'])}"
            )

            if analysis["optimization_suggestions"]:
                click.echo(f"   💡 Optimization Suggestions:")
                for suggestion in analysis["optimization_suggestions"]:
                    click.echo(f"      • {suggestion}")

            if analysis["risk_factors"]:
                click.echo(f"   ⚠️  Risk Factors:")
                for risk in analysis["risk_factors"]:
                    click.echo(f"      • {risk}")

        # JSON output option
        if ctx.obj["output_format"] == "json":
            click.echo(f"\n{format_output(simulation, 'json')}")

    except Exception as e:
        click.echo(f"❌ Simulation failed: {e}", err=True)


@simulate.command("token")
@click.argument("source")
@click.argument("destination")
@click.argument("amount", type=float)
@click.argument("metagraph_id")
@click.option("--detailed", "-d", is_flag=True, help="Show detailed analysis")
@click.pass_context
@handle_errors
def simulate_token(ctx, source, destination, amount, metagraph_id, detailed):
    """Simulate a metagraph token transfer transaction."""
    net = Network(ctx.obj["network"])

    try:
        # Convert amount (assuming 8 decimals like DAG)
        amount_tokens = int(amount * 1e8)

        # Run simulation
        simulation = Transactions.simulate_token_transfer(
            source=source,
            destination=destination,
            amount=amount_tokens,
            metagraph_id=metagraph_id,
            network=net,
            detailed_analysis=detailed,
        )

        # Display results
        click.echo(f"🪙 Token Transfer Simulation")
        click.echo(f"{'='*40}")
        click.echo(f"Source: {source}")
        click.echo(f"Destination: {destination}")
        click.echo(f"Amount: {amount} tokens")
        click.echo(f"Metagraph ID: {metagraph_id}")
        click.echo()

        # Success status
        if simulation["will_succeed"]:
            click.echo("✅ Transaction will succeed")
        else:
            click.echo("❌ Transaction will fail")

        click.echo(f"Success Probability: {simulation['success_probability']:.1%}")
        click.echo(f"Estimated Size: {simulation['estimated_size']} bytes")

        # Validation errors
        if simulation["validation_errors"]:
            click.echo("\n❌ Validation Errors:")
            for error in simulation["validation_errors"]:
                click.echo(f"   • {error}")

        # JSON output option
        if ctx.obj["output_format"] == "json":
            click.echo(f"\n{format_output(simulation, 'json')}")

    except Exception as e:
        click.echo(f"❌ Simulation failed: {e}", err=True)


@simulate.command("data")
@click.argument("source")
@click.argument("metagraph_id")
@click.option("--data", "-d", help="JSON data payload")
@click.option("--file", "-f", type=click.File("r"), help="Read data from JSON file")
@click.option("--destination", help="Destination address (defaults to source)")
@click.option("--detailed", is_flag=True, help="Show detailed analysis")
@click.pass_context
@handle_errors
def simulate_data(ctx, source, metagraph_id, data, file, destination, detailed):
    """Simulate a metagraph data submission transaction."""
    net = Network(ctx.obj["network"])

    try:
        # Get data payload
        if file:
            data_payload = json.load(file)
        elif data:
            data_payload = json.loads(data)
        else:
            # Default example data
            data_payload = {
                "type": "example",
                "timestamp": "2024-01-01T00:00:00Z",
                "value": "sample data",
            }
            click.echo("ℹ️  Using example data (use --data or --file for custom data)")

        # Run simulation
        simulation = Transactions.simulate_data_submission(
            source=source,
            data=data_payload,
            metagraph_id=metagraph_id,
            network=net,
            destination=destination,
            detailed_analysis=detailed,
        )

        # Display results
        click.echo(f"📄 Data Submission Simulation")
        click.echo(f"{'='*40}")
        click.echo(f"Source: {source}")
        click.echo(f"Destination: {destination or source}")
        click.echo(f"Metagraph ID: {metagraph_id}")
        click.echo(f"Data Size: {simulation['data_size']} bytes")
        click.echo()

        # Success status
        if simulation["will_succeed"]:
            click.echo("✅ Transaction will succeed")
        else:
            click.echo("❌ Transaction will fail")

        click.echo(f"Success Probability: {simulation['success_probability']:.1%}")
        click.echo(f"Estimated Size: {simulation['estimated_size']} bytes")

        # Validation errors
        if simulation["validation_errors"]:
            click.echo("\n❌ Validation Errors:")
            for error in simulation["validation_errors"]:
                click.echo(f"   • {error}")

        # Show data payload if small
        if simulation["data_size"] < 200:
            click.echo(f"\n📋 Data Payload:")
            click.echo(f"   {json.dumps(data_payload, indent=2)}")

        # JSON output option
        if ctx.obj["output_format"] == "json":
            click.echo(f"\n{format_output(simulation, 'json')}")

    except Exception as e:
        click.echo(f"❌ Simulation failed: {e}", err=True)


@simulate.command("cost")
@click.argument("source")
@click.argument("destination")
@click.argument("amount", type=float)
@click.option("--fee", type=float, default=0, help="Transaction fee")
@click.pass_context
@handle_errors
def simulate_cost(ctx, source, destination, amount, fee):
    """Estimate transaction cost and resource requirements."""
    net = Network(ctx.obj["network"])

    try:
        # Create mock transaction for cost estimation
        amount_ng = int(amount * 1e8)
        fee_ng = int(fee * 1e8)

        mock_tx = {
            "source": source,
            "destination": destination,
            "amount": amount_ng,
            "fee": fee_ng,
            "salt": 12345678,
        }

        # Get cost estimate
        cost_estimate = estimate_transaction_cost(net, mock_tx)

        # Display results
        click.echo(f"💰 Transaction Cost Estimation")
        click.echo(f"{'='*40}")
        click.echo(f"Transaction Size: {cost_estimate['estimated_size_bytes']} bytes")
        click.echo(
            f"Network Fee: {cost_estimate['estimated_fee']} (Constellation is feeless)"
        )
        click.echo(f"Processing Time: {cost_estimate['estimated_processing_time']}")
        click.echo(
            f"Bandwidth Required: {cost_estimate['network_bandwidth_required']} bytes"
        )
        click.echo(f"Storage Footprint: {cost_estimate['storage_footprint']} bytes")

        # JSON output option
        if ctx.obj["output_format"] == "json":
            click.echo(f"\n{format_output(cost_estimate, 'json')}")

    except Exception as e:
        click.echo(f"❌ Cost estimation failed: {e}", err=True)


# =====================
# Streaming Commands
# =====================


@cli.group()
def stream():
    """Real-time event streaming commands."""
    if not STREAMING_AVAILABLE:
        click.echo(
            "❌ Streaming not available. Install with: pip install websockets", err=True
        )
        sys.exit(1)


@stream.command("transactions")
@click.option("--addresses", "-a", multiple=True, help="Filter by addresses")
@click.option("--tx-types", "-t", multiple=True, help="Filter by transaction types")
@click.option(
    "--duration",
    "-d",
    type=int,
    default=60,
    help="Stream duration in seconds (0 for unlimited)",
)
@click.option("--output-file", "-o", help="Save events to file")
@click.pass_context
@handle_errors
def stream_transactions_cmd(ctx, addresses, tx_types, duration, output_file):
    """Stream live transactions from the network."""
    if not STREAMING_AVAILABLE:
        click.echo(
            "❌ Streaming not available. Install with: pip install websockets", err=True
        )
        return

    async def run_stream():
        click.echo(f"🔄 Starting transaction stream on {ctx.obj['network']}...")
        if addresses:
            click.echo(f"📍 Filtering addresses: {', '.join(addresses)}")
        if tx_types:
            click.echo(f"🔍 Filtering transaction types: {', '.join(tx_types)}")
        if duration > 0:
            click.echo(f"⏱️  Duration: {duration} seconds")
        else:
            click.echo("⏱️  Duration: unlimited (Ctrl+C to stop)")
        click.echo()

        # Output file handling
        output_file_handle = None
        if output_file:
            output_file_handle = open(output_file, "w")
            click.echo(f"📁 Saving events to: {output_file}")

        # Create event stream
        stream = NetworkEventStream(ctx.obj["network"])

        # Add filters if specified
        if addresses or tx_types:
            event_filter = EventFilter(
                addresses=set(addresses) if addresses else None,
                transaction_types=set(tx_types) if tx_types else None,
            )
            stream.add_filter("cli_filter", event_filter)

        # Event handler
        def handle_transaction(event):
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp)
            )

            if ctx.obj["output_format"] == "json":
                event_data = event.to_dict()
                output = json.dumps(event_data, indent=2)
            else:
                data = event.data
                output = f"[{timestamp}] 📤 Transaction Event"
                output += f"\n  Hash: {data.get('hash', 'N/A')}"
                output += f"\n  Type: {data.get('transaction_type', 'N/A')}"
                output += f"\n  From: {data.get('source', 'N/A')}"
                output += f"\n  To: {data.get('destination', 'N/A')}"
                output += f"\n  Amount: {data.get('amount', 0) / 1e8:.8f} DAG"
                output += f"\n  Network: {event.network}"
                output += "\n" + "-" * 50

            click.echo(output)

            # Save to file if specified
            if output_file_handle:
                output_file_handle.write(output + "\n")
                output_file_handle.flush()

        # Register event handler
        stream.on(EventType.TRANSACTION, handle_transaction)

        try:
            # Connect and start streaming
            await stream.connect()

            # Stream for specified duration
            if duration > 0:
                await asyncio.sleep(duration)
            else:
                # Stream indefinitely
                while True:
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            click.echo("\n🛑 Streaming stopped by user")
        finally:
            await stream.disconnect()
            if output_file_handle:
                output_file_handle.close()
                click.echo(f"📁 Events saved to: {output_file}")

            # Show statistics
            stats = stream.get_stats()
            click.echo(f"\n📊 Stream Statistics:")
            click.echo(f"  Events received: {stats['events_received']}")
            click.echo(f"  Events filtered: {stats['events_filtered']}")
            click.echo(f"  Uptime: {stats['uptime']:.1f} seconds")
            click.echo(f"  Reconnections: {stats['reconnections']}")

    # Run the async stream
    asyncio.run(run_stream())


@stream.command("balance")
@click.argument("addresses", nargs=-1, required=True)
@click.option(
    "--poll-interval",
    "-i",
    type=float,
    default=10.0,
    help="Polling interval in seconds",
)
@click.option(
    "--duration",
    "-d",
    type=int,
    default=300,
    help="Stream duration in seconds (0 for unlimited)",
)
@click.option("--output-file", "-o", help="Save balance changes to file")
@click.pass_context
@handle_errors
def stream_balance_cmd(ctx, addresses, poll_interval, duration, output_file):
    """Stream balance changes for specified addresses."""
    if not STREAMING_AVAILABLE:
        click.echo(
            "❌ Streaming not available. Install with: pip install websockets", err=True
        )
        return

    async def run_balance_stream():
        click.echo(f"💰 Starting balance tracking on {ctx.obj['network']}...")
        click.echo(f"📍 Tracking addresses: {', '.join(addresses)}")
        click.echo(f"⏱️  Poll interval: {poll_interval} seconds")
        if duration > 0:
            click.echo(f"⏱️  Duration: {duration} seconds")
        else:
            click.echo("⏱️  Duration: unlimited (Ctrl+C to stop)")
        click.echo()

        # Output file handling
        output_file_handle = None
        if output_file:
            output_file_handle = open(output_file, "w")
            click.echo(f"📁 Saving balance changes to: {output_file}")

        # Create event stream and balance tracker
        stream = NetworkEventStream(ctx.obj["network"])
        tracker = BalanceTracker(ctx.obj["network"])

        # Track specified addresses
        for address in addresses:
            try:
                tracker.track_address(address)
            except Exception as e:
                click.echo(f"❌ Invalid address {address}: {e}", err=True)
                return

        # Event handler for balance changes
        def handle_balance_change(event):
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp)
            )

            if ctx.obj["output_format"] == "json":
                event_data = event.to_dict()
                output = json.dumps(event_data, indent=2)
            else:
                data = event.data
                change = data.get("change", 0)
                change_str = (
                    f"+{change / 1e8:.8f}" if change > 0 else f"{change / 1e8:.8f}"
                )

                output = f"[{timestamp}] 💰 Balance Change"
                output += f"\n  Address: {data.get('address', 'N/A')}"
                output += f"\n  Old Balance: {data.get('old_balance', 0) / 1e8:.8f} DAG"
                output += f"\n  New Balance: {data.get('new_balance', 0) / 1e8:.8f} DAG"
                output += f"\n  Change: {change_str} DAG"
                output += f"\n  Network: {event.network}"
                output += "\n" + "-" * 50

            click.echo(output)

            # Save to file if specified
            if output_file_handle:
                output_file_handle.write(output + "\n")
                output_file_handle.flush()

        # Register event handler
        stream.on(EventType.BALANCE_CHANGE, handle_balance_change)

        try:
            # Connect and start streaming
            await stream.connect()
            await tracker.start(stream)

            # Stream for specified duration
            if duration > 0:
                await asyncio.sleep(duration)
            else:
                # Stream indefinitely
                while True:
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            click.echo("\n🛑 Balance tracking stopped by user")
        finally:
            await tracker.stop()
            await stream.disconnect()
            if output_file_handle:
                output_file_handle.close()
                click.echo(f"📁 Balance changes saved to: {output_file}")

            # Show statistics
            stats = stream.get_stats()
            click.echo(f"\n📊 Stream Statistics:")
            click.echo(f"  Events received: {stats['events_received']}")
            click.echo(f"  Uptime: {stats['uptime']:.1f} seconds")

    # Run the async balance stream
    asyncio.run(run_balance_stream())


@stream.command("events")
@click.option("--event-types", "-t", multiple=True, help="Event types to stream")
@click.option("--addresses", "-a", multiple=True, help="Filter by addresses")
@click.option(
    "--duration", "-d", type=int, default=60, help="Stream duration in seconds"
)
@click.option("--output-file", "-o", help="Save events to file")
@click.pass_context
@handle_errors
def stream_events_cmd(ctx, event_types, addresses, duration, output_file):
    """Stream all network events."""
    if not STREAMING_AVAILABLE:
        click.echo(
            "❌ Streaming not available. Install with: pip install websockets", err=True
        )
        return

    async def run_event_stream():
        click.echo(f"🌊 Starting event stream on {ctx.obj['network']}...")
        if event_types:
            click.echo(f"🔍 Event types: {', '.join(event_types)}")
        if addresses:
            click.echo(f"📍 Filtering addresses: {', '.join(addresses)}")
        click.echo(f"⏱️  Duration: {duration} seconds")
        click.echo()

        # Output file handling
        output_file_handle = None
        if output_file:
            output_file_handle = open(output_file, "w")
            click.echo(f"📁 Saving events to: {output_file}")

        # Create event stream
        stream = NetworkEventStream(ctx.obj["network"])

        # Add filters if specified
        if addresses:
            event_filter = EventFilter(addresses=set(addresses))
            stream.add_filter("cli_filter", event_filter)

        # Generic event handler
        def handle_event(event):
            timestamp = time.strftime(
                "%Y-%m-%d %H:%M:%S", time.localtime(event.timestamp)
            )

            if ctx.obj["output_format"] == "json":
                event_data = event.to_dict()
                output = json.dumps(event_data, indent=2)
            else:
                output = f"[{timestamp}] 🎯 {event.event_type.value.upper()} Event"
                output += f"\n  Network: {event.network}"
                output += f"\n  Source: {event.source}"
                output += f"\n  Data: {json.dumps(event.data, indent=2)}"
                output += "\n" + "-" * 50

            click.echo(output)

            # Save to file if specified
            if output_file_handle:
                output_file_handle.write(output + "\n")
                output_file_handle.flush()

        # Register handlers for specified event types or all
        if event_types:
            for event_type_str in event_types:
                try:
                    event_type = EventType(event_type_str)
                    stream.on(event_type, handle_event)
                except ValueError:
                    click.echo(f"❌ Unknown event type: {event_type_str}", err=True)
                    return
        else:
            # Register for all event types
            for event_type in EventType:
                stream.on(event_type, handle_event)

        try:
            # Connect and start streaming
            await stream.connect()
            await asyncio.sleep(duration)

        except KeyboardInterrupt:
            click.echo("\n🛑 Event streaming stopped by user")
        finally:
            await stream.disconnect()
            if output_file_handle:
                output_file_handle.close()
                click.echo(f"📁 Events saved to: {output_file}")

            # Show statistics
            stats = stream.get_stats()
            click.echo(f"\n📊 Stream Statistics:")
            click.echo(f"  Events received: {stats['events_received']}")
            click.echo(f"  Events filtered: {stats['events_filtered']}")
            click.echo(f"  Uptime: {stats['uptime']:.1f} seconds")

    # Run the async event stream
    asyncio.run(run_event_stream())


# =====================
# Batch Operations Commands
# =====================


@cli.group()
def batch():
    """Batch operations for enhanced REST performance."""
    pass


@batch.command("balances")
@click.argument("addresses", nargs=-1, required=True)
@click.option("--output-file", "-o", help="Save results to file")
@click.pass_context
@handle_errors
def batch_balances_cmd(ctx, addresses, output_file):
    """Get balances for multiple addresses in a single request."""
    if len(addresses) == 0:
        click.echo("❌ No addresses provided", err=True)
        return

    if len(addresses) > 100:
        click.echo("❌ Maximum 100 addresses allowed per batch", err=True)
        return

    click.echo(f"🔄 Getting balances for {len(addresses)} addresses...")

    try:
        network = Network(ctx.obj["network"])
        balances = network.get_multi_balance(list(addresses))

        # Calculate totals
        total_balance = sum(balances.values())
        funded_addresses = [addr for addr, balance in balances.items() if balance > 0]

        # Display results
        click.echo(f"\n📊 Batch Balance Results:")
        click.echo(f"  Total addresses: {len(addresses)}")
        click.echo(f"  Funded addresses: {len(funded_addresses)}")
        click.echo(f"  Total balance: {total_balance / 1e8:.8f} DAG")
        click.echo()

        if ctx.obj["output_format"] == "json":
            output_data = {
                "addresses": balances,
                "summary": {
                    "total_addresses": len(addresses),
                    "funded_addresses": len(funded_addresses),
                    "total_balance": total_balance,
                    "network": ctx.obj["network"],
                },
            }
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(output_data, f, indent=2)
                click.echo(f"📁 Results saved to: {output_file}")
            else:
                click.echo(json.dumps(output_data, indent=2))
        else:
            # Pretty format
            for address, balance in balances.items():
                status = "💰" if balance > 0 else "⚪"
                click.echo(f"{status} {address}: {balance / 1e8:.8f} DAG")

            if output_file:
                with open(output_file, "w") as f:
                    for address, balance in balances.items():
                        f.write(f"{address},{balance}\n")
                click.echo(f"📁 Results saved to: {output_file}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@batch.command("overview")
@click.argument("address")
@click.option(
    "--include-transactions", "-t", is_flag=True, help="Include recent transactions"
)
@click.pass_context
@handle_errors
def batch_overview_cmd(ctx, address, include_transactions):
    """Get comprehensive address overview in a single request."""
    click.echo(f"🔄 Getting overview for {address}...")

    try:
        network = Network(ctx.obj["network"])
        overview = network.get_address_overview(address)

        if ctx.obj["output_format"] == "json":
            click.echo(json.dumps(overview, indent=2))
        else:
            # Pretty format
            click.echo(f"\n📊 Address Overview:")
            click.echo(f"  Address: {overview['address']}")
            click.echo(f"  Balance: {overview['balance'] / 1e8:.8f} DAG")
            click.echo(f"  Ordinal: {overview['ordinal']}")
            click.echo(f"  Transactions: {len(overview['transactions'])}")
            click.echo(f"  Execution time: {overview['execution_time']:.3f}s")
            click.echo(f"  Success: {'✅' if overview['success'] else '❌'}")

            if include_transactions and overview["transactions"]:
                click.echo(f"\n📋 Recent Transactions:")
                for tx in overview["transactions"][:5]:  # Show first 5
                    amount = tx.get("amount", 0)
                    click.echo(
                        f"  • {tx.get('hash', 'N/A')[:16]}... ({amount / 1e8:.8f} DAG)"
                    )

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@batch.command("transactions")
@click.argument("addresses", nargs=-1, required=True)
@click.option("--limit", "-l", type=int, default=10, help="Transactions per address")
@click.option("--output-file", "-o", help="Save results to file")
@click.pass_context
@handle_errors
def batch_transactions_cmd(ctx, addresses, limit, output_file):
    """Get recent transactions for multiple addresses."""
    if len(addresses) == 0:
        click.echo("❌ No addresses provided", err=True)
        return

    if len(addresses) > 50:
        click.echo("❌ Maximum 50 addresses allowed for transaction batch", err=True)
        return

    click.echo(f"🔄 Getting transactions for {len(addresses)} addresses...")

    try:
        network = Network(ctx.obj["network"])
        transactions = network.get_multi_transactions(list(addresses), limit)

        # Calculate totals
        total_transactions = sum(len(txs) for txs in transactions.values())
        active_addresses = [addr for addr, txs in transactions.items() if len(txs) > 0]

        # Display results
        click.echo(f"\n📊 Batch Transaction Results:")
        click.echo(f"  Total addresses: {len(addresses)}")
        click.echo(f"  Active addresses: {len(active_addresses)}")
        click.echo(f"  Total transactions: {total_transactions}")
        click.echo()

        if ctx.obj["output_format"] == "json":
            output_data = {
                "transactions": transactions,
                "summary": {
                    "total_addresses": len(addresses),
                    "active_addresses": len(active_addresses),
                    "total_transactions": total_transactions,
                    "network": ctx.obj["network"],
                },
            }
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(output_data, f, indent=2)
                click.echo(f"📁 Results saved to: {output_file}")
            else:
                click.echo(json.dumps(output_data, indent=2))
        else:
            # Pretty format
            for address, txs in transactions.items():
                status = "📤" if len(txs) > 0 else "⚪"
                click.echo(f"{status} {address}: {len(txs)} transactions")
                if len(txs) > 0:
                    for tx in txs[:3]:  # Show first 3 transactions
                        amount = tx.get("amount", 0)
                        click.echo(
                            f"    • {tx.get('hash', 'N/A')[:12]}... ({amount / 1e8:.8f} DAG)"
                        )
                    if len(txs) > 3:
                        click.echo(f"    ... and {len(txs) - 3} more")

            if output_file:
                with open(output_file, "w") as f:
                    for address, txs in transactions.items():
                        for tx in txs:
                            f.write(
                                f"{address},{tx.get('hash', 'N/A')},{tx.get('amount', 0)}\n"
                            )
                click.echo(f"📁 Results saved to: {output_file}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@batch.command("custom")
@click.argument("operations_file", type=click.File("r"))
@click.option("--output-file", "-o", help="Save results to file")
@click.pass_context
@handle_errors
def batch_custom_cmd(ctx, operations_file, output_file):
    """Execute custom batch operations from JSON file."""
    click.echo("🔄 Loading custom batch operations...")

    try:
        # Load operations from file
        operations_data = json.load(operations_file)

        if not isinstance(operations_data, list):
            click.echo("❌ Operations file must contain a JSON array", err=True)
            return

        # Convert to batch operations
        operations = []
        for i, op_data in enumerate(operations_data):
            if not isinstance(op_data, dict):
                click.echo(f"❌ Operation {i} must be a JSON object", err=True)
                return

            operation_type = op_data.get("operation")
            params = op_data.get("params", {})
            op_id = op_data.get("id", f"op_{i}")

            try:
                batch_op = create_batch_operation(operation_type, params, op_id)
                operations.append(batch_op)
            except ValueError as e:
                click.echo(f"❌ Invalid operation {i}: {e}", err=True)
                return

        if len(operations) == 0:
            click.echo("❌ No valid operations found", err=True)
            return

        click.echo(f"🔄 Executing {len(operations)} batch operations...")

        # Execute batch request
        network = Network(ctx.obj["network"])
        response = network.batch_request(operations)

        # Display results
        click.echo(f"\n📊 Batch Execution Results:")
        click.echo(f"  Total operations: {response.summary['total_operations']}")
        click.echo(f"  Successful: {response.summary['successful_operations']}")
        click.echo(f"  Failed: {response.summary['failed_operations']}")
        click.echo(f"  Success rate: {response.summary['success_rate']:.1f}%")
        click.echo(f"  Execution time: {response.summary['execution_time']:.3f}s")

        if ctx.obj["output_format"] == "json":
            output_data = {
                "results": [
                    {
                        "id": result.id,
                        "operation": result.operation.value,
                        "success": result.success,
                        "data": result.data,
                        "error": result.error,
                    }
                    for result in response.results
                ],
                "summary": response.summary,
            }
            if output_file:
                with open(output_file, "w") as f:
                    json.dump(output_data, f, indent=2)
                click.echo(f"📁 Results saved to: {output_file}")
            else:
                click.echo(json.dumps(output_data, indent=2))
        else:
            # Pretty format
            click.echo(f"\n📋 Operation Results:")
            for result in response.results:
                status = "✅" if result.success else "❌"
                click.echo(f"{status} {result.id} ({result.operation.value})")
                if not result.success:
                    click.echo(f"    Error: {result.error}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# GraphQL Commands
@cli.group()
def graphql():
    """GraphQL query and subscription commands."""
    pass


@graphql.command("query")
@click.option("--query", "-q", help="GraphQL query string")
@click.option("--file", "-f", type=click.File("r"), help="Read query from file")
@click.option("--variables", "-v", help="Query variables as JSON string")
@click.option("--operation", "-o", help="Operation name")
@click.option("--output-file", help="Save results to file")
@click.pass_context
@handle_errors
def graphql_query_cmd(ctx, query, file, variables, operation, output_file):
    """Execute a GraphQL query."""
    if not query and not file:
        click.echo("❌ Either --query or --file must be provided", err=True)
        return

    # Import GraphQL functionality
    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient, GraphQLQuery

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    # Get query string
    if file:
        query = file.read()

    # Parse variables
    query_variables = {}
    if variables:
        try:
            query_variables = json.loads(variables)
        except json.JSONDecodeError:
            click.echo("❌ Invalid JSON in variables", err=True)
            return

    click.echo("🔄 Executing GraphQL query...")

    try:
        client = GraphQLClient(ctx.obj["network"])

        # Create query object
        gql_query = GraphQLQuery(
            query=query, variables=query_variables, operation_name=operation
        )

        # Execute query
        response = client.execute(gql_query)

        # Handle response
        if response.is_successful:
            click.echo("✅ Query executed successfully")

            if ctx.obj["output_format"] == "json":
                output_data = {
                    "data": response.data,
                    "execution_time": response.execution_time,
                    "errors": response.errors if response.errors else None,
                }

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                    click.echo(f"📁 Results saved to: {output_file}")
                else:
                    click.echo(json.dumps(output_data, indent=2))
            else:
                # Pretty format
                click.echo(f"⏱️  Execution time: {response.execution_time:.3f}s")
                click.echo("\n📊 Query Results:")
                click.echo(json.dumps(response.data, indent=2))

                if response.errors:
                    click.echo("\n⚠️  Warnings:")
                    for error in response.errors:
                        click.echo(f"  • {error.get('message', 'Unknown error')}")
        else:
            click.echo("❌ Query failed")
            for error in response.errors:
                click.echo(f"  Error: {error.get('message', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@graphql.command("account")
@click.argument("address")
@click.option(
    "--include-transactions", is_flag=True, help="Include transaction history"
)
@click.option("--include-balances", is_flag=True, help="Include metagraph balances")
@click.option("--output-file", help="Save results to file")
@click.pass_context
@handle_errors
def graphql_account_cmd(
    ctx, address, include_transactions, include_balances, output_file
):
    """Get comprehensive account data using GraphQL."""
    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient
        from .graphql_builder import build_account_query

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    click.echo(f"🔄 Getting account data for {address}...")

    try:
        # Build comprehensive account query
        query = build_account_query(address, include_transactions, include_balances)

        # Execute query
        client = GraphQLClient(ctx.obj["network"])
        response = client.execute(query)

        if response.is_successful and response.data:
            account_data = response.data.get("account", {})

            if ctx.obj["output_format"] == "json":
                output_data = {
                    "account": account_data,
                    "execution_time": response.execution_time,
                }

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                    click.echo(f"📁 Results saved to: {output_file}")
                else:
                    click.echo(json.dumps(output_data, indent=2))
            else:
                # Pretty format
                balance = account_data.get("balance", 0)
                click.echo(f"📍 Address: {account_data.get('address', address)}")
                click.echo(f"💰 Balance: {balance / 1e8:.8f} DAG")

                if include_transactions and "transactions" in account_data:
                    txs = account_data["transactions"]
                    click.echo(f"📜 Recent transactions: {len(txs)}")
                    for tx in txs[:5]:  # Show first 5
                        amount = tx.get("amount", 0)
                        click.echo(
                            f"  • {tx.get('hash', 'N/A')[:12]}... ({amount / 1e8:.8f} DAG)"
                        )

                if include_balances and "metagraphBalances" in account_data:
                    mg_balances = account_data["metagraphBalances"]
                    click.echo(f"🏛️  Metagraph balances: {len(mg_balances)}")
                    for mb in mg_balances[:3]:  # Show first 3
                        balance = mb.get("balance", 0)
                        symbol = mb.get("tokenSymbol", "Unknown")
                        click.echo(f"  • {symbol}: {balance / 1e8:.8f}")

                click.echo(f"⏱️  Execution time: {response.execution_time:.3f}s")
        else:
            click.echo("❌ Failed to get account data")
            for error in response.errors:
                click.echo(f"  Error: {error.get('message', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@graphql.command("metagraph")
@click.argument("metagraph_id")
@click.option("--include-holders", is_flag=True, help="Include holder information")
@click.option(
    "--include-transactions", is_flag=True, help="Include transaction history"
)
@click.option("--output-file", help="Save results to file")
@click.pass_context
@handle_errors
def graphql_metagraph_cmd(
    ctx, metagraph_id, include_holders, include_transactions, output_file
):
    """Get comprehensive metagraph data using GraphQL."""
    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient
        from .graphql_builder import build_metagraph_query

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    click.echo(f"🔄 Getting metagraph data for {metagraph_id}...")

    try:
        # Build comprehensive metagraph query
        query = build_metagraph_query(
            metagraph_id, include_holders, include_transactions
        )

        # Execute query
        client = GraphQLClient(ctx.obj["network"])
        response = client.execute(query)

        if response.is_successful and response.data:
            metagraph_data = response.data.get("metagraph", {})

            if ctx.obj["output_format"] == "json":
                output_data = {
                    "metagraph": metagraph_data,
                    "execution_time": response.execution_time,
                }

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                    click.echo(f"📁 Results saved to: {output_file}")
                else:
                    click.echo(json.dumps(output_data, indent=2))
            else:
                # Pretty format
                click.echo(f"🏛️  Metagraph: {metagraph_data.get('name', 'Unknown')}")
                click.echo(f"🆔 ID: {metagraph_data.get('id', metagraph_id)}")
                click.echo(f"🪙 Token: {metagraph_data.get('tokenSymbol', 'N/A')}")

                total_supply = metagraph_data.get("totalSupply", 0)
                if total_supply:
                    click.echo(f"📊 Total Supply: {total_supply / 1e8:.8f}")

                if include_holders and "holders" in metagraph_data:
                    holders = metagraph_data["holders"]
                    click.echo(f"👥 Holders: {len(holders)}")
                    for holder in holders[:5]:  # Show top 5
                        balance = holder.get("balance", 0)
                        click.echo(
                            f"  • {holder.get('address', 'N/A')[:12]}... ({balance / 1e8:.8f})"
                        )

                if include_transactions and "transactions" in metagraph_data:
                    txs = metagraph_data["transactions"]
                    click.echo(f"📜 Recent transactions: {len(txs)}")
                    for tx in txs[:5]:  # Show first 5
                        amount = tx.get("amount", 0)
                        tx_type = tx.get("type", "unknown")
                        click.echo(
                            f"  • {tx.get('hash', 'N/A')[:12]}... ({tx_type}, {amount / 1e8:.8f})"
                        )

                click.echo(f"⏱️  Execution time: {response.execution_time:.3f}s")
        else:
            click.echo("❌ Failed to get metagraph data")
            for error in response.errors:
                click.echo(f"  Error: {error.get('message', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@graphql.command("portfolio")
@click.argument("addresses", nargs=-1, required=True)
@click.option("--output-file", help="Save results to file")
@click.pass_context
@handle_errors
def graphql_portfolio_cmd(ctx, addresses, output_file):
    """Get portfolio data for multiple addresses using GraphQL."""
    if len(addresses) == 0:
        click.echo("❌ No addresses provided", err=True)
        return

    if len(addresses) > 20:
        click.echo("❌ Maximum 20 addresses allowed for portfolio query", err=True)
        return

    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient
        from .graphql_builder import build_portfolio_query

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    click.echo(f"🔄 Getting portfolio data for {len(addresses)} addresses...")

    try:
        # Build portfolio query
        query = build_portfolio_query(list(addresses))

        # Execute query
        client = GraphQLClient(ctx.obj["network"])
        response = client.execute(query)

        if response.is_successful and response.data:
            accounts_data = response.data.get("accounts", [])

            if ctx.obj["output_format"] == "json":
                output_data = {
                    "accounts": accounts_data,
                    "execution_time": response.execution_time,
                }

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                    click.echo(f"📁 Results saved to: {output_file}")
                else:
                    click.echo(json.dumps(output_data, indent=2))
            else:
                # Pretty format
                total_balance = 0
                click.echo("\n📊 Portfolio Summary:")

                for account in accounts_data:
                    address = account.get("address", "N/A")
                    balance = account.get("balance", 0)
                    total_balance += balance

                    click.echo(f"📍 {address}")
                    click.echo(f"  💰 Balance: {balance / 1e8:.8f} DAG")

                    if "transactions" in account:
                        tx_count = len(account["transactions"])
                        click.echo(f"  📜 Recent transactions: {tx_count}")

                click.echo(f"\n💎 Total Portfolio: {total_balance / 1e8:.8f} DAG")
                click.echo(f"⏱️  Execution time: {response.execution_time:.3f}s")
        else:
            click.echo("❌ Failed to get portfolio data")
            for error in response.errors:
                click.echo(f"  Error: {error.get('message', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@graphql.command("network")
@click.option("--output-file", help="Save results to file")
@click.pass_context
@handle_errors
def graphql_network_cmd(ctx, output_file):
    """Get comprehensive network status using GraphQL."""
    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient
        from .graphql_builder import build_network_status_query

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    click.echo("🔄 Getting network status...")

    try:
        # Build network status query
        query = build_network_status_query()

        # Execute query
        client = GraphQLClient(ctx.obj["network"])
        response = client.execute(query)

        if response.is_successful and response.data:
            network_data = response.data.get("network", {})

            if ctx.obj["output_format"] == "json":
                output_data = {
                    "network": network_data,
                    "execution_time": response.execution_time,
                }

                if output_file:
                    with open(output_file, "w") as f:
                        json.dump(output_data, f, indent=2)
                    click.echo(f"📁 Results saved to: {output_file}")
                else:
                    click.echo(json.dumps(output_data, indent=2))
            else:
                # Pretty format
                click.echo(f"🌐 Network: {ctx.obj['network']}")
                click.echo(f"📊 Status: {network_data.get('status', 'Unknown')}")
                click.echo(f"🏢 Node Count: {network_data.get('nodeCount', 'N/A')}")
                click.echo(f"🔧 Version: {network_data.get('version', 'N/A')}")

                if "latestBlock" in network_data:
                    block = network_data["latestBlock"]
                    click.echo(f"📦 Latest Block: {block.get('height', 'N/A')}")
                    click.echo(f"  Hash: {block.get('hash', 'N/A')[:16]}...")

                if "metrics" in network_data:
                    metrics = network_data["metrics"]
                    click.echo("📈 Network Metrics:")
                    if "transactionRate" in metrics:
                        click.echo(
                            f"  📝 Transaction Rate: {metrics['transactionRate']} tx/s"
                        )
                    if "totalTransactions" in metrics:
                        click.echo(
                            f"  📊 Total Transactions: {metrics['totalTransactions']:,}"
                        )
                    if "activeAddresses" in metrics:
                        click.echo(
                            f"  👥 Active Addresses: {metrics['activeAddresses']:,}"
                        )

                click.echo(f"⏱️  Execution time: {response.execution_time:.3f}s")
        else:
            click.echo("❌ Failed to get network status")
            for error in response.errors:
                click.echo(f"  Error: {error.get('message', 'Unknown error')}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@graphql.command("playground")
@click.option("--port", "-p", default=8080, help="Port for GraphQL playground")
@click.pass_context
@handle_errors
def graphql_playground_cmd(ctx, port):
    """Start a GraphQL playground for interactive queries."""
    try:
        from .graphql import GRAPHQL_AVAILABLE, GraphQLClient

        if not GRAPHQL_AVAILABLE:
            click.echo(
                "❌ GraphQL functionality not available. Install optional dependencies.",
                err=True,
            )
            return
    except ImportError:
        click.echo(
            "❌ GraphQL functionality not available. Install optional dependencies.",
            err=True,
        )
        return

    click.echo(f"🚀 Starting GraphQL playground on port {port}...")
    click.echo(f"🌐 Network: {ctx.obj['network']}")
    click.echo("📝 Example queries available in the playground")
    click.echo("🛑 Press Ctrl+C to stop")

    # Simple HTTP server for GraphQL playground
    try:
        import http.server
        import socketserver
        import webbrowser
        from threading import Timer

        # Create a simple HTML playground
        playground_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Constellation GraphQL Playground</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .query-area {{ width: 100%; height: 300px; font-family: monospace; }}
        .result-area {{ width: 100%; height: 400px; font-family: monospace; background: #f5f5f5; }}
        button {{ padding: 10px 20px; margin: 10px 0; font-size: 16px; }}
        .examples {{ margin: 20px 0; }}
        .example {{ margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌌 Constellation GraphQL Playground</h1>
        <p>Network: <strong>{ctx.obj['network']}</strong></p>
        
        <div class="examples">
            <h3>Example Queries (click to use):</h3>
            <div class="example" onclick="setQuery(accountQuery)">
                <strong>Account Portfolio:</strong> Get account balance and transactions
            </div>
            <div class="example" onclick="setQuery(networkQuery)">
                <strong>Network Status:</strong> Get current network information
            </div>
            <div class="example" onclick="setQuery(metagraphQuery)">
                <strong>Metagraph Overview:</strong> Get metagraph information
            </div>
        </div>
        
        <h3>Query:</h3>
        <textarea id="query" class="query-area" placeholder="Enter your GraphQL query here..."></textarea>
        
        <h3>Variables (JSON):</h3>
        <textarea id="variables" style="width: 100%; height: 100px; font-family: monospace;" placeholder='{{"address": "DAG123..."}}' ></textarea>
        
        <button onclick="executeQuery()">Execute Query</button>
        <button onclick="clearAll()">Clear</button>
        
        <h3>Result:</h3>
        <textarea id="result" class="result-area" readonly></textarea>
    </div>
    
    <script>
        const accountQuery = `query AccountPortfolio($address: String!) {{
  account(address: $address) {{
    address
    balance
    transactions(first: 10) {{
      hash
      amount
      timestamp
      destination
    }}
    metagraphBalances {{
      metagraphId
      balance
      tokenSymbol
    }}
  }}
}}`;

        const networkQuery = `query NetworkStatus {{
  network {{
    status
    nodeCount
    version
    latestBlock {{
      hash
      height
      timestamp
    }}
    metrics {{
      transactionRate
      totalTransactions
      activeAddresses
    }}
  }}
}}`;

        const metagraphQuery = `query MetagraphOverview($id: String!) {{
  metagraph(id: $id) {{
    id
    name
    tokenSymbol
    totalSupply
    holderCount
    validators {{
      address
      stake
    }}
  }}
}}`;

        function setQuery(query) {{
            document.getElementById('query').value = query;
        }}
        
        function clearAll() {{
            document.getElementById('query').value = '';
            document.getElementById('variables').value = '';
            document.getElementById('result').value = '';
        }}
        
        function executeQuery() {{
            const query = document.getElementById('query').value;
            const variables = document.getElementById('variables').value;
            
            if (!query.trim()) {{
                alert('Please enter a query');
                return;
            }}
            
            // For this demo, we'll show a mock response
            const mockResponse = {{
                "data": {{
                    "message": "This is a demo playground. Use the CLI commands to execute real queries.",
                    "example": "constellation graphql query --query 'query {{ network {{ status }} }}'"
                }}
            }};
            
            document.getElementById('result').value = JSON.stringify(mockResponse, null, 2);
        }}
    </script>
</body>
</html>
        """

        # Write HTML to temp file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            f.write(playground_html)
            temp_file = f.name

        # Open in browser
        def open_browser():
            webbrowser.open(f"file://{temp_file}")

        Timer(1.0, open_browser).start()

        click.echo(f"📱 Opening playground in your default browser...")
        click.echo(f"📄 Playground file: {temp_file}")
        click.echo("💡 This is a demo playground. Use CLI commands for real queries:")
        click.echo(
            "   constellation graphql query --query 'query { network { status } }'"
        )

        # Keep the server running
        input("Press Enter to close playground...")

        # Cleanup
        os.unlink(temp_file)

    except Exception as e:
        click.echo(f"❌ Error starting playground: {e}", err=True)


# Main entry point
def main():
    """Main CLI entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
