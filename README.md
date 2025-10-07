# 교재 코드 수정 안내 (Notice of Code Correction)

독자 여러분, 안녕하십니까?

교재 **60page~63page**에 서술된 **"5. Node(Agent) 함수 정의"** 부분의 코드에 수정 사항이 발견되었습니다. 이에 수정된 내용을 반영하여 `conditional_edges.py` 파일을 다시 업로드하였습니다.

학습에 혼선을 드린 점 사과드리며, 아래 첨부된 수정 코드와 실행 결과를 참조하여 주시기 바랍니다.

---

### 📖 교재 60page~63page: "5. Node(Agent) 함수 정의" 수정된 코드

```python
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
    return {"messages":[AIMessage(content=f"초기 문의 분석: 초기 문의는 {inquiry_type}유형 입니다.")], "inquiry_type": inquiry_type, "resolution_status": resolution_status}

def product_agent(state: AgentState):
    """
    제품 관련 문의를 처리한다
    """
    print("--- 제품 에이전트 실행 ---")
    # 실제로는 제품 DB 조회, FAQ 답변 생성 등의 로직 포함
    resolved = "resolved" if "가격" in state["messages"][0].content else "pending"
    return {"messages":[AIMessage(content=f"제품 관련 문의 처리 완료. Status: {resolved}")], "resolution_status":resolved}

def payment_agent(state: AgentState):
    """
    결제 관련 문의를 처리한다
    """
    print("--- 결제 에이전트 실행 ---")
    # 실제로는 결제 시스템 연동, 환불 처리 로직 포함
    resolved = "resolved" if "환불" in state["messages"][0].content else "pending"    
    return {"messages":[AIMessage(content=f"결제 관련 문의 처리 완료. Status: {resolved}")], "resolution_status": resolved}

def tech_support_agent(state: AgentState):
    """
    기술 지원 문의를 처리한다
    """
    print("--- 기술 지원 에이전트 실행 ---")
    # 실제로는 기술 문서 검색, 문제 해결 가이드 제공 로직 포함
    resolved = "resolved" if "재설치 완료" in state["messages"][0].content else "failed"
    return {"messages":[AIMessage(content=f"기술 관련 문의 처리 완료, Status: {resolved}")], "resolution_status": resolved}

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
    return {"messages":[AIMessage(content=response_content)], "feedback_needed":feedback_needed}

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
    return {"messages": [AIMessage(content="Feedback collected for system improvement.")]}
```

---

### 💻 교재 69page~71page: 수정된 코드의 실행 결과

--- 예시 1: 제품 관련 문의(성공적인 처리) ---
--- 초기 문의 분석 에이전트 실행 ---
문의 유형 : product
라우팅 결정: product 타입 문의
{'analysis_agent': {'messages': [AIMessage(content='초기 문의 분석: 초기 문의는 product유형 입니다.', additional_kwargs={}, response_metadata={})], 'inquiry_type': 'product', 'resolution_status': 'pending'}}
--- 제품 에이전트 실행 ---
{'product_agent': {'messages': [AIMessage(content='제품 관련 문의 처리 완료. Status: resolved', additional_kwargs={}, response_metadata={})], 'resolution_status': 'resolved'}}
--- 최종 응답 에이전트 실행 ---
최종 응답: 문의가 성공적으로 처리되었습니다. 더 궁금한 점이 있으시면 언제던지 문의해주세요
피드백 필요 없음. 그래프 종료
{'final_response_agent': {'messages': [AIMessage(content='문의가 성공적으로 처리되었습니다. 더 궁금한 점이  있으시면 언제던지 문의해주세요', additional_kwargs={}, response_metadata={})], 'feedback_needed': False}}   

--- 예시 2: 환불 관련 문의 (성공적인 처리) ---
--- 초기 문의 분석 에이전트 실행 ---
문의 유형 : payment
라우팅 결정: payment 타입 문의
{'analysis_agent': {'messages': [AIMessage(content='초기 문의 분석: 초기 문의는 payment유형 입니다.', additional_kwargs={}, response_metadata={})], 'inquiry_type': 'payment', 'resolution_status': 'pending'}}
--- 결제 에이전트 실행 ---
{'payment_agent': {'messages': [AIMessage(content='결제 관련 문의 처리 완료. Status: resolved', additional_kwargs={}, response_metadata={})], 'resolution_status': 'resolved'}}
--- 최종 응답 에이전트 실행 ---
최종 응답: 문의가 성공적으로 처리되었습니다. 더 궁금한 점이 있으시면 언제던지 문의해주세요
피드백 필요 없음. 그래프 종료
{'final_response_agent': {'messages': [AIMessage(content='문의가 성공적으로 처리되었습니다. 더 궁금한 점이  있으시면 언제던지 문의해주세요', additional_kwargs={}, response_metadata={})], 'feedback_needed': False}}   

--- 예시 3: 기술 지원 문의 (실패 -> 피드백 필요) ---
--- 초기 문의 분석 에이전트 실행 ---
문의 유형 : tech_support
라우팅 결정: tech_support 타입 문의
{'analysis_agent': {'messages': [AIMessage(content='초기 문의 분석: 초기 문의는 tech_support유형 입니다.', additional_kwargs={}, response_metadata={})], 'inquiry_type': 'tech_support', 'resolution_status': 'pending'}}
--- 기술 지원 에이전트 실행 ---
{'tech_support_agent': {'messages': [AIMessage(content='기술 관련 문의 처리 완료, Status: failed', additional_kwargs={}, response_metadata={})], 'resolution_status': 'failed'}}
--- 최종 응답 에이전트 실행 ---
최종 응답: 문의 처리에 어려움이 있어 추가 정보가 필요합니다. 자세한 내용을 알려주시겠어요?
피드백이 필요하므로 feedback_collection_node로 이동
{'final_response_agent': {'messages': [AIMessage(content='문의 처리에 어려움이 있어 추가 정보가 필요합니다. 자세한 내용을 알려주시겠어요?', additional_kwargs={}, response_metadata={})], 'feedback_needed': True}}     
--- 피드백 수집 / 학습 노드 실행 ---
피드백 데이터 수집: 원본 문의 '프로그램이 자꾸 오류가 나는데 재설치 말고 다른 방법은 없나요?', 최종 상태 'failed'
{'feedback_collection_node': {'messages': [AIMessage(content='Feedback collected for system improvement.', additional_kwargs={}, response_metadata={})]}}

--- 예시 4: 일반 문의 (초기 분석에서 처리) ---
--- 초기 문의 분석 에이전트 실행 ---
문의 유형 : general
라우팅 결정: general 타입 문의
{'analysis_agent': {'messages': [AIMessage(content='초기 문의 분석: 초기 문의는 general유형 입니다.', additional_kwargs={}, response_metadata={})], 'inquiry_type': 'general', 'resolution_status': 'resolved'}}        
--- 최종 응답 에이전트 실행 ---
최종 응답: 문의가 성공적으로 처리되었습니다. 더 궁금한 점이 있으시면 언제던지 문의해주세요
피드백 필요 없음. 그래프 종료
{'final_response_agent': {'messages': [AIMessage(content='문의가 성공적으로 처리되었습니다. 더 궁금한 점이  있으시면 언제던지 문의해주세요', additional_kwargs={}, response_metadata={})], 'feedback_needed': False}}
