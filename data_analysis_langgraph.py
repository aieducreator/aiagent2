### 1. 필요한 라이브러리 / 모듈 / 함수 임포트
import os
import sqlite3
import json
import asyncio
import uuid
from typing import List, Dict, Any, Annotated
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


### 2. 환경 설정

# 실행 파일 폴더 경로 가져오기
folder_path = os.path.dirname(os.path.abspath(__file__))

# OpenAI API Key 가져오기
env_file_path=os.path.join(folder_path, '.env')
load_dotenv(env_file_path)

# llm 생성하기
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# DB 파일 경로 설정하기
DB_PATH = os.path.join(folder_path, 'sales.db')


### 3. LangGraph 상태 정의 
class AnalysisState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    original_query: str = Field(default="", description="사용자의 원본 질문")
    sql_query: str = Field(default="", description="생성된 SQL 쿼리")
    sql_result: List[Dict] = Field(default_factory=list, description="SQL 실행 결과")


### 4. 핵심 도구 함수 정의

# DB 스키마 정보 생성 함수 정의
def get_db_schema_info() -> str | None:
    """데이터베이스 스키마 정보를 반환합니다."""
    if not os.path.exists(DB_PATH):
        return None
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='quarterly_sales';")
        result = cursor.fetchone()
        return result[0] if result else "테이블 정보를 찾을 수 없습니다."

# SQL 쿼리 실행 함수 정의
def execute_sql_query(sql: str) -> List[Dict] | str:
    """SQL 쿼리를 실행하고 결과를 반환합니다."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        return f"SQL 실행 오류: {e}"


### 5. LangGraph 노드(Node) 정의

async def sql_generation_node(state: AnalysisState) -> Dict[str, Any]:
    """사용자 질문을 바탕으로 SQL을 생성하는 노드"""
    print("\n[Node: SQL Generation]")
    user_query = state.messages[-1].content
    db_schema = get_db_schema_info()

    if not db_schema:
        raise FileNotFoundError(f"데이터베이스 파일({DB_PATH})이 없습니다. create_database_openapi.py를 먼저 실행해주세요.")

    prompt = f"""
    당신은 대한민국 서울시 상권분석 전문가이자 SQL 마스터입니다.
    아래 DB 스키마와 컬럼 의미를 참고하여, 사용자 질문에 가장 적합한 SQLite 쿼리를 생성해주세요.

    ### 데이터베이스 스키마:
    {db_schema}
    
    ### 주요 컬럼 의미 (영문 컬럼명 -> 한글 의미):
    - year_quarter: 기준년도분기 (예: '20241' = 2024년 1분기)
    - district_name: 상권명
    - service_category_name: 서비스 업종명
    - monthly_sales_amount: 월평균 추정 매출액
    - monthly_sales_count: 월평균 추정 매출 건수
    - midweek_sales_amount: 주중 매출액
    - weekend_sales_amount: 주말 매출액
    - sales_time_11_14: 점심시간(11시~14시) 매출액
    - sales_time_17_21: 저녁시간(17시~21시) 매출액
    - male_sales_amount: 남성 매출액
    - female_sales_amount: 여성 매출액
    - sales_by_age_30s: 30대 연령층의 매출액
    - 예를 들어, 사용자가 '점심 시간'을 언급하면 `sales_time_11_14` 컬럼을 사용해야 합니다.

    ### 사용자의 질문:
    {user_query}

    - 다른 설명 없이 오직 실행 가능한 SQLite 쿼리만 생성해주세요.
    """
    response = await llm.ainvoke(prompt)
    sql_query = response.content.strip().replace('`', '').replace('sql', '')
    print(f"-> 생성된 SQL:\n{sql_query}")
    return {"original_query": user_query, "sql_query": sql_query}

async def sql_execution_node(state: AnalysisState) -> Dict[str, Any]:
    """생성된 SQL을 실행하는 노드"""
    print("\n[Node: SQL Execution]")
    sql_query = state.sql_query
    result = await asyncio.to_thread(execute_sql_query, sql_query)
    
    if isinstance(result, str):
        raise sqlite3.Error(result)
        
    print(f"-> 실행 결과: {len(result)}개 행 조회")
    return {"sql_result": result}

async def report_generation_node(state: AnalysisState) -> Dict[str, Any]:
    """최종 보고서를 생성하고 상태를 업데이트하는 노드"""
    print("\n[Node: Report Generation]")
    original_query = state.original_query
    sql_query = state.sql_query
    sql_result = state.sql_result

    if not sql_result:
        report = "분석 결과, 해당 조건에 맞는 데이터가 없습니다."
    else:
        prompt = f"""
        당신은 전문 데이터 분석가이자 보고서 작성가입니다.
        다음은 사용자의 원본 질문과 데이터베이스에서 추출한 분석 결과입니다.
        이 데이터를 단순히 나열하지 말고, 사용자가 질문한 의도에 맞춰 의미 있는 인사이트를 도출하고, 비교 및 분석하여 상세한 최종 보고서를 마크다운 형식으로 작성해주세요.

        ### 원본 사용자 질문:
        {original_query}

        ### 데이터베이스 조회 결과 (JSON 형식):
        {json.dumps(sql_result, indent=2, ensure_ascii=False)}

        ### 최종 분석 보고서 (마크다운 형식):
        """
        response = await llm.ainvoke(prompt)
        report = response.content

    final_content = f"### 분석 보고서\n{report}\n\n---\n\n### 실행된 SQL 쿼리\n```sql\n{sql_query}\n```"
    return {"messages": [AIMessage(content=final_content)]}


### 6. 그래프 구성 및 콘솔 실행 로직 정의

async def main():
    """
    비동기 메인 함수: LangGraph를 설정하고,
    콘솔에서 사용자 입력을 받아 AI 에이전트를 실행합니다.
    """

    # 1. 체크포인트(대화 기록)를 저장할 파일 경로를 지정합니다.
    db_file = os.path.join(folder_path, "agent_checkpoint.sqlite")
    
    # 2. 'async with' 구문을 사용하여 Checkpointer를 안전하게 초기화합니다.
    async with AsyncSqliteSaver.from_conn_string(db_file) as memory:
        
        # 그래프 구성
        graph_builder = StateGraph(AnalysisState)
        graph_builder.add_node("generate_sql", sql_generation_node)
        graph_builder.add_node("execute_sql", sql_execution_node)
        graph_builder.add_node("generate_report", report_generation_node)
        graph_builder.set_entry_point("generate_sql")
        graph_builder.add_edge("generate_sql", "execute_sql")
        graph_builder.add_edge("execute_sql", "generate_report")
        graph_builder.add_edge("generate_report", END)

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

### 7. 애플리케이션 실행
if __name__ == "__main__":
    # 비동기 메인 함수 실행
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n프로그램 실행이 중단되었습니다.")