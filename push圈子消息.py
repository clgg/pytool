import requests
import csv
import os
import time
from typing import List
from typing import Any, Dict, Optional, Sequence, Tuple

# ===================== 可配置参数（根据你的需求修改） =====================
# 1. 模式选择：LOCAL（本地CSV） / REMOTE（远程下载CSV）
RUN_MODE = "LOCAL"  # 测试时改成本地模式，上线改回REMOTE

# 2. 本地CSV路径（RUN_MODE=LOCAL时生效）
LOCAL_CSV_PATH = os.path.join(os.path.dirname(__file__), "push_neibu.csv")

# 3. 远程CSV下载地址（RUN_MODE=REMOTE时生效）暂时没用
REMOTE_CSV_URL = "https://xxx.com/your-csv-file.csv"  # 真实远程CSV链接

# 4. 接口调用地址
API_URL = "https://api.opensplendid.cn/kkhc-bizcenter-schedule/push/manualOperatePush"
#API_URL = "https://test-api.opensplendid.cn/kkhc-bizcenter-schedule/push/manualOperatePush"

# API_URL = "http://127.0.0.1:5900/kkhc-bizcenter-schedule/push/manualOperatePush"

# 5. 固定参数配置（按需修改）
#PARAMS = {
#    "path": "ContentDetailPage",  # path放到params里
#    "contentId": "643",
#    "pushTaskId":36
#}
 
#PARAMS = {
#   "path":"webview",
#   "url":"https://www.baidu.com",
#   "title":"开开华彩"
#}  


#PARAMS = {
#    "path":"MingShiKeTangDetailScreen" ,
#    "backgroundDetailUrlList":"[具体图片url,url2]",
#    "category":"14",
#    "channelId":"app_Ads_push_ceshi14",
#    "caSwitchBySku":"1",
#    "from":"push"
#}


#PARAMS = {
#    "path":"PeerGroupPage" ,
#    "campId":"1583"
#}


#PARAMS = {
#    "path":"whichTable",
#    "tabIndex":"1"
#}

#PARAMS = {
#    "path":"ContentDetailPage",
#    "tabIndex":"123xxx"
#}


#PARAMS = {
#   "path":"my_worklist",
#   "index":"0"
#}

#PARAMS = {
#    "path" : "course_homework_container",
#    "campId":"123xxx",
#    "index":"1",
#    "campName":"班级名"
#}

#PARAMS = {
#    "path":"course_homework_container",
#    "campId":"123xxx",
#    "index":"0",
#    "campName":"班级名"
#}

#PARAMS = {
#    "path":"go_live_record",
#    "liveId":"123xxx",
#    "campId":"xxx"
#}


#PARAMS = {
#    "path":"course_homework_container",
#    "campId":"123xx",
#    "index":"1",
#    "campName":"班级名"
#}


PARAMS = {
    "path":"CourseResourcePage",
    "liveId":"123xxx"
}



TITLE = "3月28日，早安！"       # push标题
ALERT = "起床前先活动手脚，顺应阳气生发！"   # push描述

# 6. 批次大小（每20个一组）
BATCH_SIZE = 20

# 7. 请求超时时间（秒）
TIMEOUT = 30
# =========================================================================

def download_remote_csv(csv_url: str, save_path: str = "union_id_remote.csv") -> str:
    """
    下载远程CSV文件到本地（RUN_MODE=REMOTE时调用）
    :param csv_url: 远程CSV下载地址
    :param save_path: 本地保存路径
    :return: 本地CSV文件路径
    """
    try:
        print(f"【远程模式】开始下载CSV文件：{csv_url}")
        response = requests.get(csv_url, timeout=TIMEOUT)
        response.raise_for_status()  # 抛出HTTP错误

        # 保存CSV文件
        with open(save_path, "w", encoding="utf-8", newline="") as f:
            f.write(response.text)
        print(f"【远程模式】CSV文件下载完成，保存路径：{save_path}")
        return save_path
    except Exception as e:
        raise Exception(f"【远程模式】下载CSV失败：{str(e)}")

def get_csv_path() -> str:
    """
    根据运行模式获取CSV文件路径
    :return: 本地CSV文件路径
    """
    if RUN_MODE == "LOCAL":
        # 本地模式：检查文件是否存在
        if not os.path.exists(LOCAL_CSV_PATH):
            raise Exception(f"【本地模式】本地CSV文件不存在：{LOCAL_CSV_PATH}")
        print(f"【本地模式】使用本地CSV文件：{LOCAL_CSV_PATH}")
        return LOCAL_CSV_PATH
    elif RUN_MODE == "REMOTE":
        # 远程模式：下载并返回路径
        return download_remote_csv(REMOTE_CSV_URL)
    else:
        raise Exception(f"无效的运行模式：{RUN_MODE}，仅支持 LOCAL/REMOTE")

def read_union_id_from_csv(csv_path: str) -> List[str]:
    """
    读取CSV文件中的unionId列，返回去重后的非空列表
    :param csv_path: 本地CSV文件路径
    :return: unionId列表
    """
    union_id_list = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            # 读取CSV，指定列名为unionId
            reader = csv.DictReader(f)
            # 校验列名是否正确
            if "union_id" not in reader.fieldnames:
                raise Exception(f"CSV文件缺少必填列：union_id，当前列名：{reader.fieldnames}")

            for row in reader:
                union_id = row.get("union_id", "").strip()
                # 过滤空值和重复值
                if union_id and union_id not in union_id_list:
                    union_id_list.append(union_id)
        print(f"【CSV读取】共获取有效unionId数量：{len(union_id_list)}")
        return union_id_list
    except Exception as e:
        raise Exception(f"【CSV读取】读取CSV失败：{str(e)}")

def batch_call_api(
    union_id_list: Sequence[str],
    *,
    params: Dict[str, Any],
    title: str,
    alert: str,
    api_url: str = API_URL,
    batch_size: int = BATCH_SIZE,
    timeout: int = TIMEOUT,
) -> List[Tuple[int, int, Optional[Dict[str, Any]], Optional[str]]]:
    """
    每20个unionId为一组，调用接口
    :param union_id_list: 所有有效unionId列表
    """
    # 拆分批次
    batches = [
        list(union_id_list)[i:i + batch_size]
        for i in range(0, len(union_id_list), batch_size)
    ]
    print(f"【批次拆分】共拆分出 {len(batches)} 个批次，开始调用接口...")

    results: List[Tuple[int, int, Optional[Dict[str, Any]], Optional[str]]] = []
    # 遍历每个批次调用接口
    for batch_idx, batch_union_ids in enumerate(batches, 1):
        try:
            # 构造接口入参
            request_data = {
                "unionIdList": batch_union_ids,
                "params": params,
                "title": title,
                "alert": alert,
            }

            # 调用接口（POST请求，JSON格式）
            response = requests.post(
                url=api_url,
                json=request_data,
                timeout=timeout,
            )

            time.sleep(0.01)

            response.raise_for_status()  # 抛出HTTP错误

            # 打印批次结果
            payload = response.json()
            print(f"【批次 {batch_idx}/{len(batches)}】调用成功 | unionId数量：{len(batch_union_ids)} | 响应：{payload}")
            results.append((batch_idx, len(batch_union_ids), payload, None))
        except Exception as e:
            print(f"【批次 {batch_idx}/{len(batches)}】调用失败 | 错误信息：{str(e)}")
            results.append((batch_idx, len(batch_union_ids), None, str(e)))
            # 可选：失败后继续执行下一批次（注释掉则失败终止）
            continue
    return results


def send_push(
    *,
    union_ids: Sequence[str],
    params: Dict[str, Any],
    title: str,
    alert: str,
    api_url: str = API_URL,
    batch_size: int = BATCH_SIZE,
    timeout: int = TIMEOUT,
) -> List[Tuple[int, int, Optional[Dict[str, Any]], Optional[str]]]:
    return batch_call_api(
        union_ids,
        params=params,
        title=title,
        alert=alert,
        api_url=api_url,
        batch_size=batch_size,
        timeout=timeout,
    )

# 测试用：生成示例CSV文件（首次测试时可运行）
def generate_test_csv(save_path: str = "./union_id_test.csv", count: int = 50):
    """
    生成测试用的CSV文件（包含unionId列，共count条数据）
    :param save_path: 保存路径
    :param count: 生成的unionId数量
    """
    with open(save_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["unionId"])
        writer.writeheader()  # 写入列名
        for i in range(count):
            writer.writerow({"unionId": f"test_union_id_{i+1}"})
    print(f"【测试CSV生成】已生成测试文件：{save_path}，共{count}条数据")

if __name__ == "__main__":
    try:
        # 可选：首次测试时生成示例CSV文件（注释掉则不生成）
        # generate_test_csv(count=50)  # 生成50条测试数据，刚好拆成3个批次（20+20+10）

        # 1. 获取CSV文件路径（本地/远程）
        csv_file_path = get_csv_path()

        # 2. 读取unionId列表
        all_union_ids = read_union_id_from_csv(csv_file_path)

        # 3. 空列表校验
        if not all_union_ids:
            print("【终止】未读取到有效unionId，终止执行")
            exit(0)

        # 4. 批量调用接口
        batch_call_api(all_union_ids, params=PARAMS, title=TITLE, alert=ALERT)

        print("\n【完成】所有批次处理完成！")

        # 清理远程模式的临时文件（本地模式不清理）
        if RUN_MODE == "REMOTE" and os.path.exists("union_id_remote.csv"):
            os.remove("union_id_remote.csv")
            print("【清理】已删除远程下载的临时CSV文件")
    except Exception as e:
        print(f"\n【错误】程序执行失败：{str(e)}")
