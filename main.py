from __future__ import annotations

import importlib.util
import json
import os
import pkgutil
import random
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

    copy_pool = [
        ("早安！愿你今天顺顺利利", "新的一天，记得喝水、别太累，祝你心情明朗。"),
        ("午安！给自己一点松弛感", "忙里偷闲也很重要，愿你今天一切进展顺利。"),
        ("晚安！辛苦了", "把烦恼留给夜色，愿你一觉好眠，明天更轻松。"),
        ("祝你今天好运加倍", "愿好消息不断，事事有回应，件件有着落。"),
        ("提醒：别忘了照顾自己", "工作再忙也要吃好睡好，愿你平安喜乐。"),
        ("愿你今天被温柔以待", "遇见好人好事，心里有光，脚下有路。"),
    ]

    quick_users = [
        {"name": "东", "unionId": "oNGxt52FTTHyIgjtKr-VnrQeMwjA"},
        {"name": "剑", "unionId": "oNGxt57gtLmePLmpQDFbTVRYjy4Q"},
        {"name": "世勇", "unionId": "oNGxt5wGEF9Z2TNaJHliUBdcH-vM"},
        {"name": "白雪峰", "unionId": "oNGxt56cy_2OCR9s0SvpsIplXmIY"},
        {"name": "谷雨", "unionId": "oNGxt5yZoqP8-sI6pO0msqhdmuTg"},
        {"name": "学明", "unionId": "oNGxt53EwZsbThttkTyLY_EP8jVc"},
        {"name": "振霞", "unionId": "oNGxt58ULE81gkb7BW6ZF7RrPjK4"},
        {"name": "咏甄", "unionId": "oNGxt50y3QIxj02jWeOx6tR5G8oU"},
        {"name": "李响", "unionId": "oNGxt50-VGVttxHbvC17cNN6U2_o"},
        {"name": "力广", "unionId": "oNGxt57DNJQNFPUWcDMv8dC7pH94"},
    ]

    ui.add_head_html(
        """
        <style>
          .app_wrap{padding:18px;background:linear-gradient(180deg, rgba(15,23,42,.04) 0%, rgba(15,23,42,0) 40%);}
          .panel_title{font-size:14px;font-weight:600;color:rgba(15,23,42,.78);letter-spacing:.2px}
          .muted{color:rgba(15,23,42,.52)}
          .history_scroll{max-height:680px;overflow:auto}
          .left_panel{width:520px;flex:0 0 auto}
          .right_panel{flex:1 1 auto;min-width:0}
        </style>
        """
    )

    with ui.element("div").classes("app_wrap"):
        with ui.row().classes("w-full items-start gap-4").style("flex-wrap:nowrap"):
            with ui.column().classes("left_panel gap-3"):
                with ui.card().classes("w-full"):
                    ui.label("推送发送").classes("text-lg font-semibold")
                    ui.label("输入参数、unionId、标题与描述后点击发送").classes("text-sm muted")

                with ui.card().classes("w-full"):
                    ui.label("内容").classes("panel_title")
                    with ui.row().classes("w-full items-center gap-2"):
                        title_input = ui.input("title").classes("grow")
                        ui.button("随机切换", on_click=lambda: random_copy()).props("dense unelevated")
                    title_input.value = push_script.TITLE
                    alert_input = ui.input("alert").classes("w-full")
                    alert_input.value = push_script.ALERT

                with ui.card().classes("w-full"):
                    ui.label("目标用户").classes("panel_title")
                    union_input = ui.textarea("unionId（逗号/换行分隔，不能为空）").props("autogrow").classes("w-full").style("min-height:140px")
                    if default_union_ids:
                        union_input.value = "\n".join(default_union_ids[:50])
                    selected_container = ui.row().classes("w-full gap-2 flex-wrap mt-2")
                    ui.label("快捷加入").classes("text-xs muted mt-2")
                    quick_container = ui.grid(columns=5).classes("w-full gap-2")

                with ui.card().classes("w-full"):
                    ui.label("params").classes("panel_title")
                    ui.button("JSON 格式化", on_click=lambda: format_params()).props("dense flat")
                    params_input = ui.textarea("params (JSON)").props("autogrow").classes("w-full")
                    params_input.value = json.dumps(push_script.PARAMS, ensure_ascii=False, indent=2)

                ui.button("send", on_click=lambda: send()).props("unelevated color=primary").classes("w-full")

                with ui.card().classes("w-full"):
                    ui.label("result").classes("panel_title")
                    result_area = ui.textarea("").props("readonly autogrow").classes("w-full")

            with ui.column().classes("right_panel gap-3"):
                with ui.card().classes("w-full"):
                    ui.label("历史记录").classes("text-lg font-semibold")
                    ui.label("点击时间回填，右侧删除").classes("text-sm muted")
                history_container = ui.row().classes("w-full gap-3 history_scroll flex-wrap items-start")

    def random_copy() -> None:
        t, a = random.choice(copy_pool)
        title_input.value = t
        alert_input.value = a

    def format_params() -> None:
        try:
            obj = json.loads(params_input.value or "{}")
            params_input.value = json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _current_union_set() -> set[str]:
        return set(_parse_union_ids(union_input.value or ""))

    selected_union_ids: List[str] = _parse_union_ids(union_input.value or "")

    def _sync_from_textarea() -> None:
        nonlocal selected_union_ids
        selected_union_ids = _parse_union_ids(union_input.value or "")

    def _sync_to_textarea() -> None:
        union_input.value = "\n".join(selected_union_ids)

    def _toggle_union_id(uid: str) -> None:
        nonlocal selected_union_ids
        if uid in selected_union_ids:
            selected_union_ids = [x for x in selected_union_ids if x != uid]
        else:
            selected_union_ids = selected_union_ids + [uid]
        _sync_to_textarea()
        render_quick_users()
        render_selected()

    def _remove_union_id(uid: str) -> None:
        nonlocal selected_union_ids
        selected_union_ids = [x for x in selected_union_ids if x != uid]
        _sync_to_textarea()
        render_quick_users()
        render_selected()

    def render_selected() -> None:
        selected_container.clear()
        uid_to_name = {u["unionId"]: u["name"] for u in quick_users}
        with selected_container:
            for uid in selected_union_ids:
                name = uid_to_name.get(uid, uid[:6] + "…" + uid[-4:])
                ui.button(f"{name} ×", on_click=lambda e=None, x=uid: _remove_union_id(x)).props("dense unelevated color=secondary").classes("rounded-full")

    def render_quick_users() -> None:
        selected = set(selected_union_ids)
        quick_container.clear()
        with quick_container:
            for u in quick_users:
                uid = u["unionId"]
                name = u["name"]
                if uid in selected:
                    ui.button(f"{name} ✓", on_click=lambda e=None, x=uid: _toggle_union_id(x)).props("dense unelevated color=primary").classes("rounded-full w-full")
                else:
                    ui.button(name, on_click=lambda e=None, x=uid: _toggle_union_id(x)).props("dense outline").classes("rounded-full w-full")

    def render_history() -> None:
        history_container.clear()
        if not history:
            with history_container:
                with ui.element("div").classes("w-full").style("flex: 1 1 100%"):
                    with ui.card().classes("w-full").style("min-height:120px;width:100%"):
                        ui.label("暂无历史记录").classes("text-sm muted")
            return
        for idx, item in enumerate(history):
            with history_container:
                with ui.card().classes("w-96"):
                    with ui.row().classes("w-full items-center gap-2"):
                        ui.button(item.get("ts", "")).props("dense flat").on("click", lambda e, i=idx: load_history(i))
                        ui.label(item.get("title", "")).classes("text-sm muted")
                        ui.space()
                        ui.button("del").props("dense flat color=negative").on("click", lambda e, i=idx: delete_history(i))
                    p = item.get("params", {})
                    path = p.get("path") if isinstance(p, dict) else None
                    if path:
                        ui.label(f"path: {path}").classes("text-xs muted")

    def load_history(i: int) -> None:
        item = history[i]
        title_input.value = item.get("title", "")
        alert_input.value = item.get("alert", "")
        union_input.value = "\n".join(item.get("union_ids", []) or [])
        params_input.value = json.dumps(item.get("params", {}), ensure_ascii=False, indent=2)
        _sync_from_textarea()
        render_quick_users()
        render_selected()

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

    def _on_union_input(_: Any) -> None:
        _sync_from_textarea()
        render_quick_users()
        render_selected()

    union_input.on("input", _on_union_input)
    render_quick_users()
    render_selected()
    render_history()


ui.run(title="Push Tool", reload=False, native=True, window_size=(1000, 800))

