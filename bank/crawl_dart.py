"""
DART OpenAPI를 이용해 기업 공시 PDF를 다운로드.

사전 준비:
  1. https://opendart.fss.or.kr 에서 API 키 발급
  2. .env 파일에 DART_API_KEY 설정

사용법:
  python crawl_dart.py --corp 삼성전자 --count 3
"""

import os
import re
import zipfile
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DART_API_KEY = os.getenv("DART_API_KEY")
BASE_URL = "https://opendart.fss.or.kr/api"
DATA_DIR = Path("./data")


def search_corp_code(corp_name: str) -> str:
    """기업명으로 고유번호(corp_code) 검색."""
    url = f"{BASE_URL}/corpCode.xml"
    resp = requests.get(url, params={"crtfc_key": DART_API_KEY}, stream=True)
    resp.raise_for_status()

    zip_path = DATA_DIR / "_corpCode.zip"
    with open(zip_path, "wb") as f:
        f.write(resp.content)

    with zipfile.ZipFile(zip_path, "r") as z:
        xml_content = z.read("CORPCODE.xml").decode("utf-8")

    zip_path.unlink()

    pattern = rf"<corp_name>{re.escape(corp_name)}</corp_name>\s*<corp_code>(\d+)</corp_code>"
    match = re.search(pattern, xml_content)
    if not match:
        raise ValueError(f"'{corp_name}' 기업을 찾을 수 없습니다.")

    corp_code = match.group(1)
    print(f"기업 코드: {corp_code} ({corp_name})")
    return corp_code


def get_disclosure_list(corp_code: str, count: int = 5) -> list[dict]:
    """최근 공시 목록 조회."""
    url = f"{BASE_URL}/list.json"
    params = {
        "crtfc_key": DART_API_KEY,
        "corp_code": corp_code,
        "bgn_de": "20240101",
        "pblntf_ty": "A",  # A: 정기공시 (사업보고서 등)
        "page_count": count,
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "000":
        raise RuntimeError(f"DART API 오류: {data.get('message')}")

    return data.get("list", [])


def download_document(rcept_no: str, save_name: str) -> Path:
    """공시 원문 PDF/파일 다운로드."""
    url = f"{BASE_URL}/document.xml"
    params = {"crtfc_key": DART_API_KEY, "rcept_no": rcept_no}
    resp = requests.get(url, params=params, stream=True)
    resp.raise_for_status()

    zip_path = DATA_DIR / f"{save_name}.zip"
    with open(zip_path, "wb") as f:
        f.write(resp.content)

    # ZIP 내 파일 추출
    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.namelist():
            if member.endswith((".pdf", ".xml", ".htm")):
                extracted = DATA_DIR / f"{save_name}_{member.split('/')[-1]}"
                with open(extracted, "wb") as out:
                    out.write(z.read(member))
                print(f"저장: {extracted}")

    zip_path.unlink()
    return DATA_DIR


def crawl(corp_name: str, count: int = 3):
    if not DART_API_KEY:
        raise EnvironmentError(".env에 DART_API_KEY가 없습니다.")

    DATA_DIR.mkdir(exist_ok=True)
    print(f"\n{corp_name} 공시 수집 시작 (최근 {count}건)\n")

    corp_code = search_corp_code(corp_name)
    disclosures = get_disclosure_list(corp_code, count)

    if not disclosures:
        print("조회된 공시가 없습니다.")
        return

    for item in disclosures:
        rcept_no = item["rcept_no"]
        report_nm = item["report_nm"]
        rcept_dt = item["rcept_dt"]
        safe_name = re.sub(r"[^\w가-힣]", "_", f"{rcept_dt}_{report_nm}")

        print(f"\n[{rcept_dt}] {report_nm} (접수번호: {rcept_no})")
        try:
            download_document(rcept_no, safe_name)
        except Exception as e:
            print(f"  다운로드 실패: {e}")

    print(f"\n완료! data/ 폴더에 파일이 저장되었습니다.")
    print("다음 단계: python ingest.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DART 공시 다운로더")
    parser.add_argument("--corp", type=str, default="삼성전자", help="기업명")
    parser.add_argument("--count", type=int, default=3, help="수집할 공시 수")
    args = parser.parse_args()

    crawl(args.corp, args.count)
