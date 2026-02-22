from langchain_openai import ChatOpenAI

# The "Researcher" Model (Fast, Cheap, Parallel-friendly)
research_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# The "Thinker" Model (Deep reasoning, Synthesis)
boss_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)