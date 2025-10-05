# 필요한 함수 임포트
from typing import TypedDict, List

# 'messages'는 문자열 리스트여야 한다고 정의합니다.
class SimpleState(TypedDict):
    messages: List[str]

# 규칙에 맞게 상태를 생성 (오류 없음)
state_ok = SimpleState(messages=["첫 번째 메시지"])
print(f"올바른 TypedDict 상태: {state_ok}")

# 규칙을 위반하는 상태를 생성해 봅니다.
# 'messages'에 리스트가 아닌 문자열을 할당합니다.
state_wrong = SimpleState(messages="이건 리스트가 아니야!")
print(f"잘못된 TypedDict 상태: {state_wrong}")
# >> 실행 시점에는 아무런 오류가 발생하지 않습니다!