import os

import requests
import streamlit as st

API = os.getenv("TEXT2SQL_API_URL", "http://127.0.0.1:8000")

st.title("Text to SQL")
question = st.text_input("Ask a question about your data")

if st.button("Run query") and question:
    try:
        response = requests.post(
            f"{API}/v1/query", json={"query": question}, timeout=120
        )
        response.raise_for_status()
        st.session_state.response = response.json()
    except requests.RequestException as error:
        st.error(f"Query failed: {error}")

if "response" in st.session_state:
    response = st.session_state.response
    if response["type"] == "question":
        st.info(response["question"])
        answer = st.text_input(
            "Your answer",
            key=f"answer_{response['conversation_id']}_{hash(response['question'])}",
        )
        if st.button("Send answer") and answer:
            try:
                answer_response = requests.post(
                    f"{API}/v1/query/{response['conversation_id']}/answer",
                    json={"answer": answer},
                    timeout=120,
                )
                answer_response.raise_for_status()
                st.session_state.response = answer_response.json()
                st.rerun()
            except requests.RequestException as error:
                st.error(f"Answer failed: {error}")
    else:
        st.dataframe(response["result"])
        st.code(response["sql"], language="sql")
        st.markdown(f"**Confidence:** {response['confidence']:.2f}")
        st.write("Sanity violations:", response["sanity_violations"])

st.subheader("History")
try:
    history = requests.get(f"{API}/v1/history", timeout=10).json()
    for item in reversed(history):
        st.write(item["query"])
        st.dataframe(item["result"])
        st.code(item["sql"], language="sql")
        st.markdown(f"**Confidence:** {item['confidence']:.2f}")
        st.write("Sanity violations:", item["sanity_violations"])
except requests.RequestException:
    st.write("History unavailable")
