import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))
import unittest
import streamlit as st
from streamlit.testing.v1 import AppTest
import pytest
from fastapi.testclient import TestClient
import typing as t
from pydantic import BaseModel
from fastapi import status

class TestChatbotUI(unittest.TestCase):
    def test_ui_elements(self):
        at = AppTest.from_file("app.py")
        at.run()
        # 챗 입력창이 존재하는지 확인
        self.assertGreaterEqual(len(at.text_input), 1)
        # 전송 버튼이 존재하는지 확인
        self.assertGreaterEqual(len(at.button), 1)

# DuckDuckGo Tool 테스트 (목업)
def test_duckduckgo_tool():
    from duckduckgo_search import DDGS
    with DDGS() as ddgs:
        results = list(ddgs.text("python"))
        assert isinstance(results, list)

# Gemini LLM 테스트 (목업)
def test_gemini_llm():
    import google.generativeai as genai
    assert hasattr(genai, "GenerativeModel")

# React Agent 생성 테스트 (목업)
def test_create_react_agent():
    from langgraph.prebuilt import create_react_agent
    def dummy_tool(x):
        """Echo input x."""
        return x
    agent = create_react_agent(model="google_genai:gemini-2.0-flash", tools=[dummy_tool])
    assert agent is not None

# FastAPI 엔드포인트 테스트 (목업)
def test_fastapi_endpoint():
    from fastapi import FastAPI
    app = FastAPI()
    @app.get("/ping")
    def ping():
        return {"msg": "pong"}
    client = TestClient(app)
    response = client.get("/ping")
    assert response.status_code == 200
    assert response.json()["msg"] == "pong"

# FastAPI 백엔드 기본 구조 테스트
import app as backend

client = TestClient(backend.app)

def test_root_get():
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert "success" in body and body["success"] is True
    assert "data" in body and isinstance(body["data"], dict)
    assert "message" in body

def test_echo_post():
    payload = {"text": "hello"}
    res = client.post("/echo", json=payload)
    assert res.status_code == 200
    body = res.json()
    assert body["success"] is True
    assert body["data"]["echoed"] == "hello"

# 예외 처리 테스트
def test_not_found():
    res = client.get("/not-exist")
    assert res.status_code == 404
    body = res.json()
    assert body["success"] is False
    assert body["message"]

class TestStreamlitChatbot(unittest.TestCase):
    def setUp(self):
        self.at = AppTest.from_file("app.py")

    def test_chat_input_exists(self):
        self.at.run()
        # chat_input 위젯이 존재하는지 확인
        self.assertGreaterEqual(len(self.at.chat_input), 1)

    def test_chat_message_display(self):
        # 메시지 입력 후, chat_message에 표시되는지 확인
        self.at.chat_input[0].set_value("테스트 메시지").run()
        # user 메시지가 chat_message에 표시되는지 확인
        user_msgs = [m for m in self.at.chat_message if m.avatar == "user"]
        self.assertTrue(any("테스트 메시지" in m.markdown[0].value for m in user_msgs))

    def test_chat_history_persistence(self):
        # 여러 메시지 입력 후, 세션 상태에 누적되는지 확인
        self.at.chat_input[0].set_value("메시지1").run()
        self.at.chat_input[0].set_value("메시지2").run()
        self.assertGreaterEqual(len(self.at.session_state["messages"]), 2)

    def test_backend_api_response(self):
        # 백엔드와 연동되어 assistant 메시지가 표시되는지(에코 등) 확인
        self.at.chat_input[0].set_value("API 테스트").run()
        assistant_msgs = [m for m in self.at.chat_message if m.avatar == "assistant"]
        self.assertTrue(len(assistant_msgs) > 0)

if __name__ == "__main__":
    unittest.main() 