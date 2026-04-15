from __future__ import annotations

import importlib.util
import json
import os
import pkgutil
import time
from typing import Any, Dict, List

from nicegui import ui

import push圈子消息 as push_script

HISTORY_PATH = os.path.join(os.path.dirname(__file__), ".push_history.json")


def _load_history() -> List[Dict[str, Any]]:
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    except Exception:
        pass
    return []


def _save_history(items: List[Dict[str, Any]]) -> None:
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)


def _parse_union_ids(raw: str) -> List[str]:
    ids: List[str] = []
    for part in raw.replace(",", "\n").splitlines():
        s = part.strip()
        if s and s not in ids:
            ids.append(s)
    return ids


@ui.page("/")
def index() -> None:
    history = _load_history()

    try:
        default_union_ids = push_script.read_union_id_from_csv(push_script.get_csv_path())
    except Exception:
        default_union_ids = []

    ui.add_head_html(
        """
        <style>
          .app_wrap{padding:18px;background:linear-gradient(180deg, rgba(15,23,42,.04) 0%, rgba(15,23,42,0) 40%);}
          .panel_title{font-size:14px;font-weight:600;color:rgba(15,23,42,.78);letter-spacing:.2px}
          .muted{color:rgba(15,23,42,.52)}
          .history_scroll{max-height:680px;overflow:auto}
        </style>
        """
    )

    with ui.element("div").classes("app_wrap"):
        with ui.row().classes("w-full items-start gap-4"):
            with ui.column().classes("col grow gap-3"):
                with ui.card().classes("w-full"):
                    ui.label("推送发送").classes("text-lg font-semibold")
                    ui.label("输入参数、unionId、标题与描述后点击发送").classes("text-sm muted")

                with ui.card().classes("w-full"):
                    ui.label("内容").classes("panel_title")
                    title_input = ui.input("title").classes("w-full")
                    title_input.value = push_script.TITLE
                    alert_input = ui.input("alert").classes("w-full")
                    alert_input.value = push_script.ALERT

                with ui.card().classes("w-full"):
                    ui.label("目标用户").classes("panel_title")
                    union_input = ui.textarea("unionId（逗号/换行分隔，不能为空）").props("autogrow").classes("w-full")
                    if default_union_ids:
                        union_input.value = "\n".join(default_union_ids[:50])

                with ui.card().classes("w-full"):
                    ui.label("params").classes("panel_title")
                    params_input = ui.textarea("params (JSON)").props("autogrow").classes("w-full")
                    params_input.value = json.dumps(push_script.PARAMS, ensure_ascii=False, indent=2)

                ui.button("send", on_click=lambda: send()).props("unelevated color=primary").classes("w-full")

                with ui.card().classes("w-full"):
                    ui.label("result").classes("panel_title")
                    result_area = ui.textarea("").props("readonly autogrow").classes("w-full")

            with ui.column().classes("col-4 gap-3"):
                with ui.card().classes("w-full"):
                    ui.label("历史记录").classes("text-lg font-semibold")
                    ui.label("点击时间回填，右侧删除").classes("text-sm muted")
                history_container = ui.column().classes("w-full gap-2 history_scroll")

    def render_history() -> None:
        history_container.clear()
        for idx, item in enumerate(history):
            with history_container:
                with ui.card().classes("w-full"):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.button(item.get("ts", "")).props("dense flat").on("click", lambda e, i=idx: load_history(i))
                        ui.label(item.get("title", "")).classes("text-sm muted")
                        ui.space()
                        ui.button("del").props("dense flat color=negative").on("click", lambda e, i=idx: delete_history(i))

    def load_history(i: int) -> None:
        item = history[i]
        title_input.value = item.get("title", "")
        alert_input.value = item.get("alert", "")
        union_input.value = "\n".join(item.get("union_ids", []) or [])
        params_input.value = json.dumps(item.get("params", {}), ensure_ascii=False, indent=2)

    def delete_history(i: int) -> None:
        history.pop(i)
        _save_history(history)
        render_history()

    def send() -> None:
        nonlocal history
        try:
            params = json.loads(params_input.value or "{}")
            if not isinstance(params, dict):
                raise ValueError("params must be object")
            union_ids = _parse_union_ids(union_input.value or "")
            if not union_ids:
                raise ValueError("unionId 不能为空")
            results = push_script.send_push(
                union_ids=union_ids,
                params=params,
                title=title_input.value or "",
                alert=alert_input.value or "",
            )
            result_area.value = json.dumps(results, ensure_ascii=False, indent=2)
            item = {
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "params": params,
                "union_ids": union_ids,
                "title": title_input.value or "",
                "alert": alert_input.value or "",
            }
            history = [item] + history
            history = history[:50]
            _save_history(history)
            render_history()
        except Exception as e:
            result_area.value = str(e)

    render_history()


ui.run(title="Push Tool", reload=False, native=True, window_size=(1000, 800))

