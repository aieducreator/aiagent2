# 필요한 함수 임포트
from pydantic import BaseModel, ValidationError
from typing import List

# 'messages'는 문자열 리스트여야 한다고 Pydantic 모델로 정의합니다.
class SmartState(BaseModel):
    messages: List[str]

# 규칙에 맞게 상태를 생성 (오류 없음)
state_ok = SmartState(messages=["첫 번째 메시지"])
print(f"올바른 Pydantic 상태: {state_ok}")

# 규칙을 위반하는 상태를 생성해 봅니다.
try:
    # 'messages'에 리스트가 아닌 문자열을 할당하여 오류를 유발합니다.
    state_wrong = SmartState(messages="이건 리스트가 아니야!")
except ValidationError as e:
    print(f"\nPydantic 유효성 검사 오류 발생!")
    print(e)
    # >> 코드 실행 즉시 유효성 검사 오류(ValidationError)가 발생합니다!