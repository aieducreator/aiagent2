### 1. 필요한 모듈 / 함수 임포트
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage
import operator


### 2. 환경 설정: API 키 불러오기
load_dotenv()


### 3. 그래프 상태 정의
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    inquiry_type: str
    resolution_status: str
    feedback_needed: bool


### 4. LLM 설정
llm = ChatOpenAI(model='gpt-4o-mini', temperature=0.7)


### 5. Node(Agent) 함수 정의
def analysis_agent(state: AgentState):
    """
    고객의 문의를 분석하여 문의 유형을 분류한다
    """
    print("--- 초기 문의 분석 에이전트 실행 ---")
    user_message = state["messages"][-1].content
    inquiry_type = "unknown"
    resolution_status = "pending"

    # 간단한 키워드 기반 분류(실제로는 LLM을 통해 정교하게 분류)
    if "제품" in user_message or "서비스" in user_message:
        inquiry_type="product"
    elif "결제" in user_message or "환불" in user_message or "청구" in user_message:
        inquiry_type="payment"
    elif "오류" in user_message or "작동" in user_message or "설치" in user_message:
        inquiry_type="tech_support"
    else:
        inquiry_type="general"
        # 일반 문의는 초기 분석에서 바로 처리된 것으로 간주하여 최종 응답으로 연결
        resolution_status="resolved"
        
    print(f"문의 유형 : {inquiry_type}")
    # inquiry_type과 함꼐 resolution_status도 반환하도록 수정 
    return {"inquiry_type": inquiry_type, "resolution_status": resolution_status, "messages":[HumanMessage(content=f"초기 문의 분석: 초기 문의는 {inquiry_type}유형 입니다.")]}

def product_agent(state: AgentState):
    """
    제품 관련 문의를 처리한다
    """
    print("--- 제품 에이전트 실행 ---")
    # 실제로는 제품 DB 조회, FAQ 답변 생성 등의 로직 포함
    resolved = "resolved" if "가격" in state["messages"][-1].content else "pending"
    return {"resolution_status":resolved, "messages":[HumanMessage(content=f"제품 관련 문의 처리 완료. Status: {resolved}")]}

def payment_agent(state: AgentState):
    """
    결제 관련 문의를 처리한다
    """
    print("--- 결제 에이전트 실행 ---")
    # 실제로는 결제 시스템 연동, 환불 처리 로직 포함
    resolved = "resolved" if "환불" in state["messages"][-1].content else "pending"
    return {"resolution_status": resolved, "messages":[HumanMessage(content=f"결제 관련 문의 처리 완료. Status: {resolved}")]}


def tech_support_agent(state: AgentState):
    """
    기술 지원 문의를 처리한다
    """
    print("--- 기술 지원 에이전트 실행 ---")
    # 실제로는 기술 문서 검색, 문제 해결 가이드 제공 로직 포함
    resolved = "resolved" if "재설치" in state["messages"][-1].content else "failed"
    return {"resolution_status": resolved, "messages":[HumanMessage(content=f"기술 관련 문의 처리 완료, Status: {resolved}")]}

def final_response_agent(state: AgentState):
    """
    최종 응답을 생성하고 필요한 경우 피드백 여부를 결정한다
    """
    print("--- 최종 응답 에이전트 실행 ---")
    resolution_status = state["resolution_status"]
    feedback_needed = False
    response_content = ""

    if resolution_status=="resolved":
        response_content="문의가 성공적으로 처리되었습니다. 더 궁금한 점이 있으시면 언제던지 문의해주세요"
    elif resolution_status=="pending":
        response_content="문의가 접수되었으며 추가 확인이 필요합니다. 곧 담당자가 연락드릴 예정입니다."
    elif resolution_status=="failed":
        response_content="문의 처리에 어려움이 있어 추가 정보가 필요합니다. 자세한 내용을 알려주시겠어요?"
        feedback_needed=True  # 처리 실패 시 피드백 필요

    print(f"최종 응답: {response_content}")
    return {"messages":[HumanMessage(content=response_content)], "feedback_needed":feedback_needed}

def feedback_collection_node(state: AgentState):
    """
    # 피드백을 수집하거나 학습 데이터를 기록하는 노드
    # 여기에 데이터베이스 저장, 로그 기록, 특정 에이전트의 가중치 조정 로직 등
      "학습"에 필요한 데이터 수집 및 분석 로직이 들어갈 수 있음 
    """
    print("--- 피드백 수집 / 학습 노드 실행 ---")
    # 최초 문의 내용
    user_query = state["messages"][0].content
    # 최종 상태
    final_status = state["resolution_status"]
    print(f"피드백 데이터 수집: 원본 문의 '{user_query}', 최종 상태 '{final_status}'")
    # 실제 시스템에서는 이 정보를 바탕으로 LLM 프롬프트, tool 사용 로직 등을 개선할 수 있습니다.
    return {"messages": [HumanMessage(content="Feedback collected for system improvement.")]}


### 6. 조건부 라우팅 함수 정의
def route_inquiry(state: AgentState):
    """
    문의 유형에 따라 다음 에이전트로 라우팅한다
    """
    inquiry_type = state["inquiry_type"]
    print(f"라우팅 결정: {inquiry_type} 타입 문의")
    if inquiry_type=="product":
        return "product_agent"
    elif inquiry_type=="payment":
        return "payment_agent"
    elif inquiry_type=="tech_support":
        return "tech_support_agent"
    else: # general or unknown
        # 초기 분석에서 처리할 수 없는 경우 바로 최종 응답으로 연결
        return "final_response_agent"
    
def route_to_feedback_or_end(state: AgentState):
    """
    피드백이 필요한지 여부에 따라 다음 노드로 라우팅하거나 종료한다
    """
    if state["feedback_needed"]:
        print("피드백이 필요하므로 feedback_collection_node로 이동")
        return "feedback_collection_node"
    else:
        print("피드백 필요 없음. 그래프 종료")
        return END
    

### 7. 그래프 구성

## 7-1 그래프 상태 객체 생성
workflow = StateGraph(AgentState)

## 7-2 노드 추가
workflow.add_node("analysis_agent", analysis_agent)
workflow.add_node("product_agent", product_agent)
workflow.add_node("payment_agent", payment_agent)
workflow.add_node("tech_support_agent", tech_support_agent)
workflow.add_node("final_response_agent", final_response_agent)
workflow.add_node("feedback_collection_node", feedback_collection_node)

## 7-3 시작점 설정
workflow.set_entry_point("analysis_agent")

## 7-4 edge 추가
# 1) 초기 분석 에이전트에서 문의 유형에 따라 분기
workflow.add_conditional_edges(
    "analysis_agent",
    route_inquiry,
    {
        "product_agent": "product_agent",
        "payment_agent": "payment_agent",
        "tech_support_agent": "tech_support_agent",
        "final_response_agent": "final_response_agent"
    }
) 

# 2) 각 전문 에이전트에서 최종 응답 에이전트로 연결
workflow.add_edge("product_agent", "final_response_agent")
workflow.add_edge("payment_agent", "final_response_agent")
workflow.add_edge("tech_support_agent", "final_response_agent")

# 3) 최종 응답 에이전트에서 피드백 여부에 따라 분기 또는 종료
workflow.add_conditional_edges(
    "final_response_agent",
    # 피드백 필요 여부에 따른 라우팅 함수
    route_to_feedback_or_end,
    {
        "feedback_collection_node": "feedback_collection_node",
        END: END
    }
)

# 4) 피드백 수집 노드에서 종료로 연결
workflow.add_edge("feedback_collection_node", END)


## 7-5 그래프 컴파일: : 그래프를 실행 가능한 구조로 변환
app = workflow.compile()


### 8. 그래프 실행 예시
print("--- 예시 1: 제품 관련 문의(성공적인 처리) ---")
inputs1 = {"messages": [HumanMessage(content="제품의 가격 정보가 궁금합니다.")]}
for s in app.stream(inputs1):
    print(s)

print(f"\n--- 예시 2: 환불 관련 문의 (성공적인 처리) ---")
inputs2 = {"messages": [HumanMessage(content="주문한 물품을 환불하고 싶습니다.")]}
for s in app.stream(inputs2):
    print(s)

print("\n--- 예시 3: 기술 지원 문의 (실패 -> 피드백 필요) ---")
inputs3 = {"messages": [HumanMessage(content="프로그램이 자꾸 오류가 나는데 재설치 말고 다른 방법은 없나요?")]}
for s in app.stream(inputs3):
    print(s)

print("\n--- 예시 4: 일반 문의 (초기 분석에서 처리) ---")
inputs4 = {"messages": [HumanMessage(content="안녕하세요, 문의할 것이 있습니다.")]}
for s in app.stream(inputs4):
    print(s)    

