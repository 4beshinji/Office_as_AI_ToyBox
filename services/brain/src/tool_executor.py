"""
Tool Executor: Routes tool calls through Sanitizer validation to handlers.
"""
import json
from typing import Dict, Any
from loguru import logger


class ToolExecutor:
    def __init__(self, sanitizer, mcp_bridge, dashboard_client, world_model, task_queue):
        self.sanitizer = sanitizer
        self.mcp = mcp_bridge
        self.dashboard = dashboard_client
        self.world_model = world_model
        self.task_queue = task_queue

    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call with validation.

        Returns:
            {"success": True, "result": "..."} or {"success": False, "error": "..."}
        """
        # Validate through Sanitizer
        is_safe, reason = self.sanitizer.validate_tool_call(tool_name, arguments)
        if not is_safe:
            logger.warning(f"Tool call REJECTED: {tool_name} - {reason}")
            return {"success": False, "error": reason}

        try:
            if tool_name == "create_task":
                return await self._handle_create_task(arguments)
            elif tool_name == "send_device_command":
                return await self._handle_device_command(arguments)
            elif tool_name == "get_zone_status":
                return await self._handle_get_zone_status(arguments)
            elif tool_name == "get_active_tasks":
                return await self._handle_get_active_tasks()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return {"success": False, "error": str(e)}

    async def _handle_create_task(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create a task via DashboardClient and register with TaskQueueManager."""
        title = args.get("title", "")
        description = args.get("description", "")
        bounty = args.get("bounty", 1000)
        urgency = args.get("urgency", 2)
        zone = args.get("zone")

        # Parse task_types from comma-separated string
        task_types_str = args.get("task_types", "general")
        task_types = [t.strip() for t in task_types_str.split(",") if t.strip()]

        result = await self.dashboard.create_task(
            title=title,
            description=description,
            bounty=bounty,
            urgency=urgency,
            zone=zone,
            task_types=task_types,
        )

        if result and result.get("id"):
            task_id = result["id"]

            # Register with TaskQueueManager for scheduling
            if self.task_queue:
                await self.task_queue.add_task(
                    task_id=task_id,
                    title=title,
                    urgency=urgency,
                    zone=zone,
                )

            return {
                "success": True,
                "result": f"タスク '{title}' を作成しました (ID: {task_id}, 報酬: {bounty}pt)",
            }
        else:
            return {"success": False, "error": "タスクの作成に失敗しました"}

    async def _handle_device_command(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Send command to edge device via MCPBridge."""
        agent_id = args.get("agent_id", "")
        tool_name = args.get("tool_name", "")

        # Parse arguments (may be JSON string or dict)
        inner_args = args.get("arguments", "{}")
        if isinstance(inner_args, str):
            try:
                inner_args = json.loads(inner_args)
            except (json.JSONDecodeError, TypeError):
                inner_args = {}

        result = await self.mcp.call_tool(agent_id, tool_name, inner_args)
        return {
            "success": True,
            "result": f"デバイスコマンド実行完了: {agent_id}/{tool_name} -> {json.dumps(result, ensure_ascii=False)}",
        }

    async def _handle_get_zone_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed zone status from WorldModel."""
        zone_id = args.get("zone_id", "")
        zone = self.world_model.get_zone(zone_id)

        if zone is None:
            return {"success": False, "error": f"ゾーン '{zone_id}' が見つかりません"}

        # Build status string
        lines = [f"ゾーン: {zone_id}"]

        if zone.occupancy.person_count > 0:
            lines.append(f"在室: {zone.occupancy.person_count}名 ({zone.occupancy.activity_summary})")
        else:
            lines.append("在室: 無人")

        env = zone.environment
        if env.temperature is not None:
            lines.append(f"気温: {env.temperature:.1f}℃ ({env.thermal_comfort})")
        if env.humidity is not None:
            lines.append(f"湿度: {env.humidity:.0f}%")
        if env.co2 is not None:
            lines.append(f"CO2: {env.co2}ppm{'（換気必要）' if env.is_stuffy else ''}")
        if env.illuminance is not None:
            lines.append(f"照度: {env.illuminance:.0f}lux")

        if zone.devices:
            for dev_id, dev in zone.devices.items():
                lines.append(f"デバイス {dev.device_type}({dev_id}): {dev.power_state}")

        return {"success": True, "result": "\n".join(lines)}

    async def _handle_get_active_tasks(self) -> Dict[str, Any]:
        """Get active tasks from DashboardClient."""
        tasks = await self.dashboard.get_active_tasks()
        if not tasks:
            return {"success": True, "result": "アクティブなタスクはありません"}

        summaries = []
        for t in tasks[:10]:  # Limit to 10
            title = t.get("title", "")
            status = t.get("status", "")
            summaries.append(f"- {title} (status: {status})")

        return {
            "success": True,
            "result": f"アクティブなタスク ({len(tasks)}件):\n" + "\n".join(summaries),
        }
