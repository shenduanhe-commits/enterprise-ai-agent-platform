from mcp.server.mcpserver import MCPServer

ORDERS: dict[str, dict[str, str]] = {
    "ORD-1001": {"status": "已发货", "item": "笔记本", "amount": "8999"},
    "ORD-1002": {"status": "待付款", "item": "键盘", "amount": "199"},
}


def lookup_order(order_id: str) -> str:
    """Look up a mock sales order by ID, for example ORD-1001."""
    key = order_id.strip().upper()
    row = ORDERS.get(key)
    if row is None:
        return f"查无此单 {key}"
    return (
        f"订单 {key}：状态={row['status']} 商品={row['item']} 金额={row['amount']}"
    )


def create_order_server() -> MCPServer:
    server = MCPServer("eaap-orders")
    server.add_tool(lookup_order)
    return server


def main() -> None:
    create_order_server().run()


if __name__ == "__main__":
    main()
