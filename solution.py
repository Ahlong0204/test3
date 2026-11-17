"""안내서비스.csv를 카테고리별로 분리하고 집계하는 자동화 도구.

사용법:
    python solution.py

입력:  첨부/안내서비스.csv
출력:  출력_카테고리별/<카테고리명>.csv  (카테고리별 행 분리)
       결과_카테고리집계.csv             (카테고리별 건수·대표 문의기관)
표준 라이브러리(csv, pathlib, collections, sys)만 사용합니다.
"""
import csv
import sys
from collections import Counter, OrderedDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "첨부" / "안내서비스.csv"
OUTPUT_DIR = BASE_DIR / "출력_카테고리별"
SUMMARY_CSV = BASE_DIR / "결과_카테고리집계.csv"

CATEGORY_COLUMN = "카테고리"
ORG_COLUMN = "문의기관"
UNCLASSIFIED = "미분류"
INVALID_FILENAME_CHARS = '\\/:*?"<>|'


def safe_filename(name: str) -> str:
    """파일명으로 쓸 수 없는 문자를 밑줄로 바꿉니다."""
    cleaned = "".join("_" if ch in INVALID_FILENAME_CHARS else ch for ch in name).strip()
    return cleaned or UNCLASSIFIED


def read_rows(path: Path):
    """CSV를 읽어 (헤더, 행 목록)을 반환합니다. BOM이 있어도 안전하게 읽습니다."""
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def split_by_category(rows):
    """카테고리 값을 기준으로 행을 묶습니다. 처음 나온 순서를 유지합니다."""
    groups = OrderedDict()
    for row in rows:
        category = (row.get(CATEGORY_COLUMN) or "").strip() or UNCLASSIFIED
        groups.setdefault(category, []).append(row)
    return groups


def write_category_files(groups, fieldnames):
    """카테고리별 CSV 파일을 만들고 집계용 요약 목록을 반환합니다."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    summary = []
    for category, items in groups.items():
        path = OUTPUT_DIR / f"{safe_filename(category)}.csv"
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(items)

        # 대표 문의기관: 가장 많이 나온 기관 (동률이면 먼저 나온 기관)
        orgs = Counter((r.get(ORG_COLUMN) or "").strip() for r in items)
        representative = orgs.most_common(1)[0][0] or "-"
        summary.append({"카테고리": category, "건수": len(items), "대표_문의기관": representative})
    return summary


def write_summary(summary):
    with SUMMARY_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["카테고리", "건수", "대표_문의기관"])
        writer.writeheader()
        writer.writerows(summary)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    if not INPUT_CSV.exists():
        print(f"[ERROR] 입력 파일을 찾을 수 없습니다: {INPUT_CSV}")
        return 1

    fieldnames, rows = read_rows(INPUT_CSV)
    groups = split_by_category(rows)

    summary = write_category_files(groups, fieldnames)
    print(f"[OK] 안내서비스 {len(rows)}건 카테고리별 분리 → 출력_카테고리별/")
    for item in summary:
        print(f" · {item['카테고리']} {item['건수']}건")

    write_summary(summary)
    print("[OK] 집계표 → 결과_카테고리집계.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
