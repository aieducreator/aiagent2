### 1. 필요한 라이브러리 / 모듈 / 함수 임포트
import os
import sys
import json
import asyncio
import uuid
from typing import Annotated, List, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from functools import partial


### 2. 환경 설정 

# 실행 파일 폴더 경로 가져오기
folder_path = os.path.dirname(os.path.abspath(__file__))

# OpenAI API Key 가져오기
env_file_path=os.path.join(folder_path, '.env')
load_dotenv(env_file_path)

# 파이썬 실행 환경 가져오기
python_command = sys.executable


### 3. LangGraph 상태 정의 
class AgentState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]



### 4. 노드(오케스트레이터) 함수 정의

async def call_analysis_expert_node(state: AgentState, tool: Any) -> Dict[str, Any]:
    """분석 전문가 서버의 도구를 직접 호출하는 단일 책임 노드"""
    user_query = state.messages[-1].content
    # 콘솔에서는 print를 통해 진행 상황을 명확히 보여줍니다.
    print(f"\n[Node: Call Analysis Expert] '{user_query}' 분석을 요청합니다...")
    
    try:
        # FastMCP 도구 호출
        response_str = await tool.ainvoke({"input_data": {"query": user_query}})
        response_data = json.loads(response_str)

        if "result" in response_data:
            report = response_data["result"].get("report", "보고서 내용이 없습니다.")
            sql = response_data["result"].get("executed_sql", "실행된 SQL 정보가 없습니다.")
            # 최종 결과물을 final_content에 저장
            final_content = f"### 분석 보고서\n{report}\n\n---\n\n### 실행된 SQL 쿼리\n```sql\n{sql}\n```"
            print("-> 분석 성공.")
        else:
            error_msg = response_data.get("error", "알 수 없는 오류가 발생했습니다.")
            final_content = f"### 분석 중 오류 발생\n- **오류 내용:** {error_msg}"
            if "executed_sql" in response_data and response_data["executed_sql"]:
                final_content += f"\n- **실패한 쿼리:** `{response_data['executed_sql']}`"
            print(f"-> 분석 실패: {error_msg}")
            
        return {"messages": [AIMessage(content=final_content)]}

    except Exception as e:
        error_content = f"오케스트레이터 시스템 오류가 발생했습니다: {e}"
        print(f"[CRITICAL] {error_content}")
        return {"messages": [AIMessage(content=error_content)]}


### 5. 그래프 구성 및 콘솔 실행 로직 

async def main():
    """
    비동기 메인 함수: MCP 클라이언트와 LangGraph를 설정하고,
    콘솔에서 사용자 입력을 받아 AI 에이전트를 실행합니다.
    """
    
    # 1. 체크포인트(대화 기록)를 저장할 파일 경로를 지정합니다.
    db_file = os.path.join(folder_path, "analyze_commercial_district_checkpoint.sqlite")
    
    # 2. 'async with' 구문을 사용하여 Checkpointer를 안전하게 초기화합니다.
    async with AsyncSqliteSaver.from_conn_string(db_file) as memory:
        # 단일 분석 전문가 서버만 관리하도록 클라이언트 설정
        client = MultiServerMCPClient({
            "DataAnalysisExpert": {
                "command": python_command, 
                "args": [os.path.join(folder_path, "data_analysis_server.py")],
                "transport": "stdio"
            }
        })
        
        print("\n--- MCP 서버로부터 분석 전문가 도구 로드 중... ---")
        tools = await client.get_tools()
        if not tools:
            print("[ERROR] 서버로부터 도구를 가져오지 못했습니다. 서버가 정상 실행 중인지 확인하세요.")
            return
        
        analysis_tool = tools[0]
        print(f"--- '{analysis_tool.name}' 도구 로드 완료 ---\n")

        # 그래프 구성: 입력 -> 분석 노드 -> 종료
        graph_builder = StateGraph(AgentState)
        graph_builder.add_node("call_analysis", partial(call_analysis_expert_node, tool=analysis_tool))
        graph_builder.set_entry_point("call_analysis")
        graph_builder.add_edge("call_analysis", END)
        
        # 파일 기반 Checkpointer를 사용하여 그래프를 컴파일합니다.
        agent_executor = graph_builder.compile(checkpointer=memory)
        
        # --- 콘솔 UI 로직 ---
        print("==================================================")
        print("      서울시 상권 분석 전문 AI 에이전트 (콘솔 모드)      ")
        print("==================================================")
        print("분석하고 싶은 내용을 질문해주세요. (종료하려면 '종료' 또는 'exit' 입력)")

        # 각 대화 세션을 위한 고유 ID 생성
        thread_id = str(uuid.uuid4())
        
        while True:
            try:
                # 사용자 입력 받기
                user_input = input("\n사용자: ")
                if user_input.lower() in ["exit", "종료"]:
                    print("AI 에이전트: 프로그램을 종료합니다.")
                    break

                config = {"configurable": {"thread_id": thread_id}}
                
                print("AI 에이전트: (분석 중...)")

                # LangGraph 에이전트 실행
                final_state = await agent_executor.ainvoke(
                    {"messages": [HumanMessage(content=user_input)]}, 
                    config=config
                )
                
                # 최종 결과 출력
                final_answer = final_state['messages'][-1].content
                print("\n" + "="*25 + " 최종 결과 " + "="*25)
                print(final_answer)
                print("="*62)

            except KeyboardInterrupt:
                print("\nAI 에이전트: 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"[CRITICAL] 예상치 못한 오류가 발생했습니다: {e}")


### 6. 애플리케이션 실행 
if __name__ == "__main__":
    # 비동기 메인 함수 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램 실행이 중단되었습니다.")