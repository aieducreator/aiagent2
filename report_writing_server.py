### 1. 환경 설정

# 필요한 함수 임포트
from typing import Dict, Any
from pydantic import BaseModel, Field
from fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# API Key 가져오기(명시적 경로 설정)
file_path = '.env'
load_dotenv(file_path)


### 2. 서버 및 LLM 설정 

# 서버 설정
mcp_server = FastMCP(name="ReportWritingExpert")

# LLM 설정
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.6)


### 3. 전문가 도구 함수 정의

# 입력 스키마 정의
class ReportInput(BaseModel):
    user_query: str = Field(description="보고서 생성을 위한 사용자의 원본 요청 문장")
    research_summary: str = Field(description="시장 조사 전문가로부터 전달받은 요약 정보")

# 전문가 도구 함수 정의
@mcp_server.tool(
    name="write_final_report",
    description="사용자 요청과 시장 조사 요약을 바탕으로, 최종 분석 보고서를 마크다운 형식으로 생성합니다."
)
def write_final_report(input_data: ReportInput) -> Dict[str, Any]:
    """
    LLM을 사용하여 분석 결과와 사용자 의도를 종합한 최종 보고서를 작성하는 전문가 도구.
    """
    print("--- [ReportWritingExpert] 최종 보고서 작성을 시작합니다. ---")
    prompt = f"""
    당신은 전문 데이터 분석가이자 보고서 작성 전문가입니다.
    다음은 사용자의 원본 요청과 그에 따라 수집된 데이터 요약입니다.
    이 요약 정보를 바탕으로, 사용자의 원래 질문 의도에 맞춰 비교, 분석, 요약 및 제언을 포함한 상세한 최종 보고서를 마크다운 형식으로 작성해주세요.
    데이터를 단순히 나열하지 말고, 비교 분석하여 의미 있는 인사이트를 도출해야 합니다.

    # 원본 사용자 요청:
    {input_data.user_query}

    # 수집된 시장 조사 요약:
    {input_data.research_summary}

    # 최종 보고서 (마크다운 형식):
    """
    try:
        response = llm.invoke(prompt)
        report_text = response.content
        return {"result": {"report_text": report_text}}
    except Exception as e:
        error_message = f"보고서 생성 중 LLM 호출 오류 발생: {e}"
        print(f"[ERROR] {error_message}")
        return {"error": error_message}


### 4. 서버 실행
if __name__ == "__main__":
    print("MCP [ReportWritingExpert] 서버가 시작되었습니다.")
    mcp_server.run()