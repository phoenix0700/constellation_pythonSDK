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
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict

try:
    import click
except ImportError:
    print("Error: 'click' library is required for CLI functionality.")
    print("Install it with: pip install click")
    sys.exit(1)

from .account import Account
from .exceptions import ConstellationError, NetworkError, ValidationError
from .metagraph import MetagraphClient
from .network import Network
from .validation import AddressValidator

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
        "public_key": acc.public_key.hex(),
        "private_key": acc.private_key.hex() if save_key else "***HIDDEN***",
    }

    if save_key:
        cli_config.set("default_private_key", acc.private_key.hex())
        click.echo("🔐 Private key saved to CLI config")

    click.echo("✅ New account created:")
    click.echo(format_output(output, ctx.obj["output_format"]))

    if not save_key:
        click.echo(f"\n🔑 Private Key (save this!): {acc.private_key.hex()}")


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
        output = {
            "address": address,
            "balance": balance_info.get("balance", "N/A"),
            "ordinal": balance_info.get("ordinal", "N/A"),
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
        output = {
            "address": address,
            "balance": balance_info.get("balance", "0"),
            "ordinal": balance_info.get("ordinal", 0),
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
    current_balance = float(balance_info.get("balance", 0))

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
        parent=balance_info.get("lastTransactionRef", {}).get("hash", ""),
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
            return await discover_metagraphs_async(production_only=production)
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


# Main entry point
def main():
    """Main CLI entry point."""
    cli(obj={})


if __name__ == "__main__":
    main()
