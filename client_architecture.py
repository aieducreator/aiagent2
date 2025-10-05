### 1. 환경 설정

# 필요한 라이브러리 / 모듈 / 함수 임포트
import os
import asyncio
import json
import sys
from langchain_mcp_adapters.client import MultiServerMCPClient

# 실행 파일 폴더 경로 설정
folder_path = os.path.dirname(os.path.abspath(__file__))


### 2. 메인 함수 정의

async def run_client():
    
    try:
        # client 생성
        client = MultiServerMCPClient({
            "GreetingServer": {
                "command": sys.executable, 
                "args": [os.path.join(folder_path, "tool_server_architecture.py")], 
                "transport": "stdio"
            }
        })
        
        # 도구 목록(list) 생성
        tools = await client.get_tools()

        # 도구 설정
        greeting_tool = tools[0]
        print(f"호출 준비 완료: {greeting_tool.name}")

        print('-'*80)

        # 서버에 요청할 Python 딕셔너리 생성
        payload = {"input_data": {"name": "박안정", "language": "한국어"}} 

        # ainvoke 함수는 이 Python 딕셔너리를, 컴퓨터가 네트워크를 통해 쉽게 주고받을 수 있는 JSON 형식의 문자열로 변환       
        print(f"서버에 요청 전송: {json.dumps(payload, ensure_ascii=False)}")

        print('-'*80)

        # 도구 실행 -> JSON 형식의 문자열
        response_str = await greeting_tool.ainvoke(payload)
        print(f"서버로부터 응답 수신: {response_str}")

        print('-'*80)

        # 서버가 보낸 JSON 문자열을 다시 Python 딕셔너리로 변환
        response_data = json.loads(response_str)
        # print(f"서버로부터 응답 수신: {json.dumps(response_data, ensure_ascii=False)}")

        # 결과 추출
        if "result" in response_data:
            print(f"최종 결과: {response_data['result']['greeting']}")
        else:
            print(f"서버에서 처리된 오류: {response_data.get('error')}")

    except Exception as e:
        # client 생성, tool 호출 등 모든 과정에서 발생할 수 있는 예외를 처리
        print("\n[CRITICAL] 클라이언트 실행 중 예측하지 못한 오류가 발생했습니다.")
        print(f"오류 유형: {type(e).__name__}")
        print(f"오류 메시지: {e}")


### 3. 메인 함수 실행
if __name__ == "__main__":
    asyncio.run(run_client())
    print("\n[SYSTEM] 클라이언트 실행이 완료되었으며, 서버 프로세스는 자동으로 종료됩니다.")