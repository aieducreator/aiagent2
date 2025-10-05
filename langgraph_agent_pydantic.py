### 1. 필요한 모듈 / 함수 임포트
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


### 2. 환경 설정(명시적 경로 설정): API 키 불러오기 
file_path = '.env'
load_dotenv(file_path)


### 3. RAG 시스템 기반 설정 (그래프 외부에서 1회 실행)

# 3-1. 데이터 로딩, 분할, 임베딩 및 벡터 저장소 구축
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
retriever = vectorstore.as_retriever(search_kwargs={'k': 1}) 

# 3-5 프롬프트 및 LLM 정의
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
def rag_node(state: AgentState):
    """RAG 체인을 실행하여 답변을 생성하는 노드"""
    question = state.messages[-1].content
    response = rag_chain.invoke(question)
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

# 6-5 그래프 컴파일: 그래프를 실행 가능한 구조로 변환
app = workflow.compile()


### 7. 에이전트 실행
inputs = {"messages": [HumanMessage(content="수강료 환불 규정이 어떻게 되나요?")]}
final_result = app.invoke(inputs)
print("--- 최종 결과 (Level 2: Pydantic 기반) ---")
print(final_result['messages'][-1].content)