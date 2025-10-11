### 1. 환경 설정

# 필요한 라이브러리 / 모듈 / 클래스 임포트
import os
import asyncio
import json
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

# 실행 파일(client_architecture.py) 폴더 경로 설정
folder_path = os.path.dirname(os.path.abspath(__file__))


### 2. 메인 함수 정의

async def run_client():
    """
    1. 기능: 도구 서버('GreetingServer')를 실행 및 관리하고, 해당 서버가 제공하는 도구를 
       원격으로 호출하여 인사 메시지를 요청한 뒤 응답을 받아 처리한다
    2. "command": sys.executable의 기능
        1) "현재 이 클라이언트 코드를 실행하고 있는 '바로 그 파이썬(현재 가상 환경)'을 사용해서,
           'tool_server_architecture.py' 파일을 실행시켜 도구 서버를 활성화해라"    
        2) 도구 서버를 클라이언트와 동일한 환경에서 실행하여 환경의 차이로 인한 오류를 방지한다
        3) 실행할 도구 서버 파일 -> "args"의 값(value) 
        4) 도구 서버와의 통신 방법 -> "transport"의 값(value)
    """
    
    try:
        # client 생성
        client = MultiServerMCPClient(
            {
                "GreetingServer": {
                    "command": sys.executable,
                    "args": [os.path.join(folder_path, "tool_server_architecture.py")],
                    "transport": "stdio"
                }
            }
        )

        # 도구 목록(list) 생성
        tools = await client.get_tools()

        # 도구 설정: 인사 메시지 생성 도구
        greeting_tool = tools[0]
        print(f"도구 목록과 명세: {greeting_tool}")
        print('-'*80)
        print(f'도구 호출 준비 완료: {greeting_tool.name}')

        print('-'*80)

        # 도구 서버에 요청할 python 딕셔너리 생성: 도구 함수(create_greeting)의 입력 값 생성
        payload = {"input_data": {"name":"박안정", "language":"한국어"}}

        # ainvoke 함수는 이 python 딕셔너리(payload)를, 클라이언트와 도구 서버간에 쉽게 주고 받을 수 있는 JSON 문자열로 변환

        # 도구 실행 -> 응답: JSON 형식의 문자열
        response_str = await greeting_tool.ainvoke(payload)
        print(f'서버로부터 응답 수신: {response_str}')

        # 서버가 보낸 JSON 문자열을 다시 python 딕셔너리로 변환
        response_data = json.loads(response_str)

        # 결과 추출
        if "result" in response_data:
            print(f"최종 결과: {response_data['result']['greeting']}")
        else:
            print(f'서버에서 처리된 오류: {response_data.get('error')}')

    # 포괄적 예외 처리
    except Exception as e:
        # client 생성, tool 호출 등 모든 과정에서 발생할 수 있는 예외를 처리
        print("\n[CRITICAL] 클라이언트 실행 중 예측하지 못한 오류가 발생했습니다.")
        print(f"오류 유형: {type(e).__name__}")        
         

### 3. 메인 함수 실행
if __name__=="__main__":
    asyncio.run(run_client())
    print(f"\n[SYSTEM] 클라이언트 실행이 완료되었으며, 서버 프로세스는 자동으로 종료됩니다.")