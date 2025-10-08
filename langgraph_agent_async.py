### 1. 필요한 라이브러리 / 모듈 / 함수 임포트
import asyncio
from dotenv import load_dotenv
from pydantic import BaseModel, Field 
from typing import Annotated, List
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver 


### 2. 환경 설정(명시적 경로 설정): API 키 불러오기 
file_path = '.env'
load_dotenv(file_path)


### 3. RAG 시스템 기반 설정 (그래프 외부에서 1회 실행)

# 3-1. 데이터 로딩
loader = TextLoader("manual.txt", encoding="utf-8")
documents = loader.load()

# 3-2. 텍스트 분할 
text_splitter = CharacterTextSplitter(separator="\n\n", chunk_size=200, chunk_overlap=0)
docs = text_splitter.split_documents(documents)

# 3-3 임베딩 모델 설정
embeddings = HuggingFaceEmbeddings(model_name="paraphrase-multilingual-MiniLM-L12-v2")

# 3-4 벡터 저장소(VectorStore) 및 리트리버(Retriever) 생성
# 관련성 높은 1개 청크 검색
vectorstore = FAISS.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={'k': 2}) 

# 3-5 프롬프트 및 LLM 설정
template = """
당신은 코드크래프터스 아카데미의 친절한 고객 지원 담당자입니다.
주어진 컨텍스트 정보를 바탕으로 고객의 질문에 명확하고 친절하게 답변해주세요.
컨텍스트에 질문에 대한 정보가 없다면, '죄송하지만 문의하신 내용에 대해서는 매뉴얼에서 정보를 찾을 수 없습니다.'라고 답변해주세요.

컨텍스트:
{context}

질문:
{question}
"""
prompt = ChatPromptTemplate.from_template(template)
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

# 3-6 RAG 체인 구성
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


### 4. 그래프 상태(Graph State) 정의
class AgentState(BaseModel):
    messages: Annotated[List[BaseMessage], operator.add] = Field(default_factory=list)


### 5. 그래프 노드(Graph Nodes) 함수 정의

""" RAG 체인을 비동기적으로 실행하여 답변을 생성하는 노드 """

async def rag_node(state: AgentState):    
    question = state.messages[-1].content
    # rag_chain -> 비동기 호출
    response = await rag_chain.ainvoke(question) 
    return {"messages": [AIMessage(content=response)]}


### 6. 그래프 구성

# 6-1 그래프 상태 객체 생성
workflow = StateGraph(AgentState)

# 6-2 노드 추가
workflow.add_node("rag_node", rag_node)

# 6-3 그래프의 시작점을 'rag_node' 노드로 설정
workflow.set_entry_point("rag_node")

# 6-4 엣지 추가
workflow.add_edge("rag_node", END)


### 7. 그래프 실행

async def main():

    """ 
    1. 체크포인트를 저장할 SQLite 데이터베이스 파일명을 설정합니다. 
    2. 'async with' 구문을 사용하여 데이터베이스 연결을 안전하게 관리합니다.
    3. 이 블록이 끝나면 memory.conn (데이터베이스 연결)이 자동으로 닫힙니다.
    """

    # 1. 체크포인트를 저장할 파일 경로를 지정합니다.
    db_file = "single_agent.sqlite"

    # 2. 'async with' 구문을 사용하여 데이터베이스 연결을 안전하게 관리합니다.
    async with AsyncSqliteSaver.from_conn_string(db_file) as memory:
        """
        # async with AsyncSqliteSaver.from_conn_string(db_file) as memory의 의미:
        비동기 방식의 SQLite 데이터베이스(db_file)를 사용하여 LangGraph의 체크포인트를 관리할 수 있는 
        AsyncSqliteSaver 인스턴스를 memory라는 이름으로 생성하고, async with 블록이 끝날 때 DB 연결이 
        안전하게 해제되도록 보장한다
        """
        
        # 그래프 컴파일 + 체크포인터 설정(그래프와 연결)
        app = workflow.compile(checkpointer=memory)   

        print("안녕하세요! 코드크래프터스 AI 에이전트입니다. 무엇을 도와드릴까요? (종료: exit)")
        print('\n')


        # 각 대화를 식별하기 위한 고유 ID 설정
        config = {"configurable": {"thread_id": "user-1234"}}

        # 그래프 실행
        while True:
            user_input = input("사용자: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            
            # HumanMessage를 포함한 리스트로 초기 상태 설정            
            initial_state = {"messages": [HumanMessage(content=user_input)]}
            print("\nAI 에이전트: (답변을 생성 중입니다...)")
            
            # 최종 결과 생성, config를 포함하여 ainvoke 호출
            # Checkpointer가 config의 thread_id를 보고 DB에서 이전 대화 내용을 자동으로 불러온다
            # 최종 결과 -> dict 자료 구조: {'messages': [HumanMessage, AIMessage,...]}
            final_result = await app.ainvoke(initial_state, config)

            # 최종 결과 값 추출
            ai_response = final_result['messages'][-1]
            final_answer = ai_response.content
            print(f"\nAI 에이전트: {final_answer}")
            print("-" * 80)

### 8. 애플리케이션 실행
if __name__ == "__main__":
    asyncio.run(main())