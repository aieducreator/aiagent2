### 1. 필요한 모듈 / 함수 임포트
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from typing import Annotated, List, Dict, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, END
import operator


### 2. LangGraph 상태 정의: Pydantic BaseModel 사용
class AgentState(BaseModel):
    # 상태 메시지 누적 구조 생성 
    messages: Annotated[List[BaseMessage], operator.add] = Field(
        default_factory=list, 
        description="대화 이력 목록 (역할, 내용 포함)"
        )
    tool_output: Optional[str] = Field(
        None, 
        description="마지막으로 실행된 도구의 결과 텍스트"
        )


### 3. 그래프 노드 정의 (상태를 입력받고 업데이트)

# 각 노드는 실행 결과를 딕셔너리로 반환: 상태 업데이트
def call_llm(state: AgentState) -> Dict:
    print("---LLM 노드 실행---")
    messages = state.messages
    # 마지막 메시지가 HumanMessage인지 확인 후 content 값 가져오기
    last_user_message = messages[-1].content if messages and isinstance(messages[-1], HumanMessage) else ""
    print(f"\n사용자의 입력: {last_user_message}")

    print("-"*80)

    # LLM의 응답 시뮬레이션 (항상 도구 사용을 지시한다고 가정)
    print(f"\nLLM: 사용자 메시지 '{last_user_message}'에 따라 도구 사용을 지시합니다.")
    # 실제는 llm의 응답 결과를 반환, 여기서는 AIMessage 클래스를 사용해서 직접 결과를 생성하고 반환    
    return {"messages":[AIMessage(content="도구 사용을 요청합니다.")]}

def call_tool(state: AgentState) -> Dict:
    print("\n---도구 노드 실행---")
    # 도구 실행을 시뮬레이션합니다.
    print("\n도구 'mock_tool' 실행 중...")
    tool_result = "도구 mock_tool 실행 결과: 데이터 처리 완료."

    # messages와 tool_output를 동시에 업데이트 할 수 있도록 결과 생성 및 변환    
    return {
        "messages": [ToolMessage(content=tool_result, tool_call_id="mock_tool_call_id_123")],
        "tool_output": tool_result
    }

def summarize_result(state: AgentState) -> Dict:
    print("\n---결과 요약 노드 실행---")
    tool_result = state.tool_output
    summary = f"\n도구 실행 결과 '{tool_result}'를 요약했습니다."    
    print(f"\n결과 요약: {summary}")    
    # 실제는 llm의 요약 결과를 반환, 여기서는 AIMessage 클래스를 사용해서 직접 결과를 생성하고 반환 
    return {"messages": [AIMessage(content=summary)]}


### 4. LangGraph 구성

## 4-1 그래프 상태 객체 생성
workflow = StateGraph(AgentState)

## 4-2 그래프 상태에 노드 추가
workflow.add_node("call_llm_node", call_llm)
workflow.add_node("call_tool_node", call_tool)
workflow.add_node("summarize_node", summarize_result)

## 4-3 시작점 설정
workflow.set_entry_point("call_llm_node")

## 4-4 에지 정의 

# LLM 실행 후 도구 호출
workflow.add_edge("call_llm_node", "call_tool_node") 
# 도구 사용 후 결과 요약
workflow.add_edge("call_tool_node", "summarize_node") 
# 결과 요약 후 종료
workflow.add_edge("summarize_node", END) 

## 4-5 그래프 컴파일: : 그래프를 실행 가능한 구조로 변환
app = workflow.compile()

print('\n')


### 5. 실행 및 결과 확인

print("=== Pydantic BaseModel 기반 에이전트 실행 ===")

# 초기 메시지 생셩 
initial_state = {"messages": [HumanMessage(content="이 작업을 시작해줘!")]}

# 단계별 실행 과정 출력
for s in app.stream(initial_state):
    print(s)
    print("-"*80)

# 최종 결과 생성 및 결과 확인
final_state_example = app.invoke(initial_state)
print(f"\n최종 상태 메시지 (Pydantic BaseModel): {final_state_example['messages']}")
print('-'*80)
print(f"최종 도구 출력 (Pydantic BaseModel): {final_state_example['tool_output']}")

print('\n')


### Pydantic의 유효성 검사 (예시: 잘못된 타입 할당 시 오류 발생)
try:
    print("[Pydantic 유효성 검사 오류 시도]")
    # messages는 List[BaseMessage] 타입이어야 하는데 문자열을 할당하여 오류 발생
    invalid_state = AgentState(messages="잘못된 타입의 메시지")
except Exception as e:
    print(f"Pydantic 유효성 검사 오류 발생: {e}")