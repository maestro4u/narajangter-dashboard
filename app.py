import math
import os
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="나라장터 입찰 대시보드")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = "***REMOVED***"

PRE_URL = "http://apis.data.go.kr/1230000/ao/HrcspSsstndrdInfoService/getPublicPrcureThngInfoServcPPSSrch"
BID_URL = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch"


class SearchRequest(BaseModel):
    start_day: Optional[str] = None
    end_day: Optional[str] = None
    regions: List[str] = [
        "서울", "강원", "경상", "대구", "울산", "부산", "국군", "공사",
        "경기", "충청", "세종", "대전", "전라", "광주", "제주"
    ]
    include_kw: List[str] = ["개발", "설계", "기본", "실시", "공모"]
    exclude_kw: List[str] = [
        "정비공사", "건설사업관리", "영향평가", "이행평가", "학교", "폐기물",
        "임차", "준공검사", "대책", "하수관", "상수관", "확장", "실태조사",
        "전시공간", "청소", "개조사업", "유지관리", "지역관리", "시설관리"
    ]
    min_budget: int = 100_000_000


def get_date_range(start_day, end_day):
    today = datetime.now()
    ed = end_day or today.strftime("%Y%m%d")
    sd = start_day or (today - timedelta(days=3)).strftime("%Y%m%d")
    return sd, ed


def pass_filter(agency, title, budget, regions, include_kw, exclude_kw, min_budget):
    a, t = (agency or ""), (title or "")
    try:
        amt = int(float(budget)) if budget else 0
    except Exception:
        amt = 0
    return (
        any(r in a for r in regions)
        and any(k in t for k in include_kw)
        and not any(k in t for k in exclude_kw)
        and amt >= min_budget
    )


def fetch_all_pages(base_url: str, start_day: str, end_day: str):
    base_params = {
        "numOfRows": "100", "pageNo": "1", "ServiceKey": API_KEY,
        "inqryDiv": "1", "inqryBgnDt": f"{start_day}0000",
        "inqryEndDt": f"{end_day}2359", "type": "json",
    }
    try:
        r = requests.get(base_url, params={**base_params, "numOfRows": "1"}, timeout=30)
        r.raise_for_status()
        total = r.json().get("response", {}).get("body", {}).get("totalCount", 0)
        if not total:
            return []
        pages = math.ceil(total / 100)
        all_items = []
        for page in range(1, pages + 1):
            resp = requests.get(base_url, params={**base_params, "pageNo": str(page)}, timeout=30)
            resp.raise_for_status()
            items = resp.json().get("response", {}).get("body", {}).get("items") or []
            all_items.extend(items)
        return all_items
    except Exception as e:
        print(f"API error: {e}")
        return []


@app.get("/")
async def root():
    return FileResponse("static/index.html")


@app.post("/api/search")
async def search(req: SearchRequest):
    sd, ed = get_date_range(req.start_day, req.end_day)

    pre_raw = fetch_all_pages(PRE_URL, sd, ed)
    pre_items = [
        item for item in pre_raw
        if item.get("bsnsDivNm") == "기술용역"
        and pass_filter(item.get("orderInsttNm"), item.get("prdctClsfcNoNm"),
                        item.get("asignBdgtAmt"), req.regions, req.include_kw,
                        req.exclude_kw, req.min_budget)
    ]

    bid_raw = fetch_all_pages(BID_URL, sd, ed)
    bid_items = [
        item for item in bid_raw
        if item.get("srvceDivNm") == "기술용역"
        and pass_filter(item.get("ntceInsttNm"), item.get("bidNtceNm"),
                        item.get("asignBdgtAmt"), req.regions, req.include_kw,
                        req.exclude_kw, req.min_budget)
    ]

    return {
        "start_day": sd, "end_day": ed,
        "pre_count": len(pre_items), "bid_count": len(bid_items),
        "pre_items": pre_items, "bid_items": bid_items,
    }


@app.get("/api/config")
async def get_config():
    return SearchRequest().dict()


app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=(port == 8000))
