import streamlit as st
import requests
from duckduckgo_search import DDGS

st.title("Vibe 챗봇")

# 세션 상태에 메시지 히스토리 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# 과거 메시지 표시
for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 사용자 입력 처리 및 백엔드 연동 (DuckDuckGo 검색)
if prompt := st.chat_input("검색어를 입력하세요"):  # 프롬프트 문구도 검색에 맞게 변경
    # 사용자 메시지 표시 및 저장
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    # FastAPI 백엔드 /search 엔드포인트에 POST 요청
    try:
        res = requests.post(
            "http://localhost:8000/search", json={"query": prompt}, timeout=10
        )
        if res.ok:
            data = res.json()
            print("DuckDuckGo 결과:", data)
            if data.get("success") and data.get("data") and data["data"].get("results"):
                results = data["data"]["results"]
                # 검색 결과를 마크다운 리스트로 포맷팅
                msg = "\n".join([
                    f"**[{item['title']}]({item['link']})**\n{item['snippet']}"
                    for item in results
                ])
            else:
                msg = "검색 결과가 없습니다."
        else:
            msg = "[오류] 서버 응답 실패"
    except Exception as e:
        msg = f"[오류] {e}"
    # 어시스턴트 메시지 표시 및 저장
    with st.chat_message("assistant"):
        st.markdown(msg)
    st.session_state["messages"].append({"role": "assistant", "content": msg})

# --- FastAPI 백엔드 기본 구조 추가 ---
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import typing as t

app = FastAPI()

# 표준 응답 포맷
class StandardResponse(BaseModel):
    success: bool
    data: t.Optional[dict] = None
    message: t.Optional[str] = None

# 예외 핸들러
@app.exception_handler(Exception)
def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=StandardResponse(success=False, data=None, message=str(exc)).model_dump(),
    )

@app.get("/")
def root():
    return StandardResponse(success=True, data={}, message="백엔드 정상 동작").model_dump()

# 예시 POST 엔드포인트
class EchoRequest(BaseModel):
    text: str

@app.post("/echo")
def echo(req: EchoRequest):
    return StandardResponse(success=True, data={"echoed": req.text}, message="ok").model_dump()

# 404 예외 핸들러 오버라이드
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(StarletteHTTPException)
def custom_http_exception_handler(request, exc):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content=StandardResponse(success=False, data=None, message="Not Found").model_dump(),
        )
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardResponse(success=False, data=None, message=exc.detail).model_dump(),
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return await request_validation_exception_handler(request, exc)

class SearchRequest(BaseModel):
    query: str

@app.post("/search")
def search(req: SearchRequest):
    try:
        results = DDGS().text(req.query, max_results=5)
        # 결과에서 title, href, body만 추출
        items = [
            {"title": r["title"], "link": r["href"], "snippet": r["body"]}
            for r in results
        ]
        return StandardResponse(success=True, data={"results": items}, message="검색 성공").model_dump()
    except Exception as e:
        return StandardResponse(success=False, data=None, message=f"검색 오류: {e}").model_dump()

print("PR 테스트용 간단 수정")

print(list(DDGS().text("아이폰 15프로", max_results=5))) 