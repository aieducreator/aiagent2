### 1. 필요한 함수 / 클래스 / 도구 임포트
from typing import Dict, Any
from pydantic import BaseModel, Field
from fastmcp import FastMCP

### 2. 도구 서버 생성
mcp_server = FastMCP(name="GreetingServer")

### 3. 도구 함수의 입력 형식 설정 
"""
# 도구 함수의 입력 데이터에 사용할 전용 자료형 설정
"""
class GreetingInput(BaseModel):
    name: str = Field(..., description="인사할 사람의 이름")
    language: str = Field(..., description="사용할 언어 ('한국어', 'English')")

### 4. 도구 함수 정의

# FastMCP 클래스의 데코레이터 -> 파이썬 함수를 '도구'로 변환하고 서버에 등록
@mcp_server.tool(
    name = "create_greeting_message",
    description = "주어진 이름과 언어로 인사 메시지를 생성합니다."
)
def create_greeting(input_data: GreetingInput) -> Dict[str, Any]:
    """
    # 기능: 주어진 이름과 언어로 인사 메시지를 생성합니다.
    - 성공 시: {"result": {"greeting": ...}}
    - 실패 시: {"error": "..."}
    형태의 딕셔너리를 반환합니다.
    """

    try:
        # "messages"는 미리 정의된 언어(key)와 인사말(value)의 대응표(lookup table)이다
        messages = {
            "한국어": f"안녕하세요. {input_data.name}님! 만나서 반갑습니다.",
            "English": f"Hello, {input_data.name}! It's a pleasure to meet you."
        } 

        # 사용자의 언어 입력(input_data.language)를 key로 사용하여, 대응표에서 인사말을 찾는다
        message = messages.get(input_data.language)

        # 성공의 결과 생성
        if not message:
            # 예상된 오류 케이스 처리: 어떤 언어가 지원되는지 알려주어 사용성을 높인다
            supported_language = list(messages.keys())
            raise ValueError(f"{input_data.language}는 지원하지 않는 언어입니다. 지원되는 언어: {supported_language}")
        else:
            # 성공 시, 정해진 프로토콜에 따라 결과 반환
            return {"result": {"greeting": message}}
        
    except Exception as e:
        # 예측하지 못한 모든 오류를 처리하여 서버가 죽지 않도록 방지
        error_message = f"인사말 생성 중 오류 발생: {str(e)}"
        print(f"[ERROR] {error_message}")

        # 실패 시, 정해진 프로토콜에 따라 에러 반환
        return {"error": error_message}
    
### 5. 서버 실행
if __name__ == "__main__":
    print("MCP GreetingServer 시작")
    mcp_server.run() 