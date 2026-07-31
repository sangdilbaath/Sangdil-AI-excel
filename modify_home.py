import re

with open("Home.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the preview section to add tabs and the toolkit
old_preview = """            render_metrics(active_df)

            st.markdown('<div class="section-label">Dataset Columns</div>', unsafe_allow_html=True)
            col_list = active_df.columns.tolist()
            
            col_expanded = st.checkbox("Show all columns as pills", value=st.session_state.show_all_cols)
            st.session_state.show_all_cols = col_expanded
            
            pills_class = "col-pills-wrap expanded" if col_expanded else "col-pills-wrap"
            pills_html = f'<div class="{pills_class}">'
            for c in col_list:
                pills_html += f'<span class="col-pill">{sanitize_col_name(c)} ({str(active_df[c].dtype)})</span>'
            pills_html += '</div>'
            st.markdown(pills_html, unsafe_allow_html=True)

            st.markdown('<div class="section-label">Dataset Preview</div>', unsafe_allow_html=True)
            
            show_all_rows = st.checkbox("Show all records", value=st.session_state.show_all_data)
            st.session_state.show_all_data = show_all_rows
            
            preview_rows = active_df if show_all_rows else active_df.head(15)
            st.dataframe(preview_rows, use_container_width=True)"""

new_preview = """            tab_preview, tab_analysis, tab_export = st.tabs(["📊 Data & Toolkit", "💬 AI Analysis", "📤 Export"])
            
            with tab_preview:
                st.markdown('<div class="section-label">Data Cleaning Toolkit</div>', unsafe_allow_html=True)
                st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                with col_btn1:
                    if st.button("🧹 Drop Missing Values", use_container_width=True, key="btn_drop_na"):
                        st.session_state.updated_df = active_df.dropna()
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Remove Duplicates", use_container_width=True, key="btn_drop_dup"):
                        st.session_state.updated_df = active_df.drop_duplicates()
                        st.rerun()
                with col_btn3:
                    if st.button("🔄 Reset to Original Data", use_container_width=True, key="btn_reset"):
                        st.session_state.updated_df = st.session_state.df.copy()
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

                render_metrics(active_df)

                st.markdown('<div class="section-label">Dataset Columns</div>', unsafe_allow_html=True)
                col_list = active_df.columns.tolist()
                
                col_expanded = st.checkbox("Show all columns as pills", value=st.session_state.show_all_cols)
                st.session_state.show_all_cols = col_expanded
                
                pills_class = "col-pills-wrap expanded" if col_expanded else "col-pills-wrap"
                pills_html = f'<div class="{pills_class}">'
                for c in col_list:
                    pills_html += f'<span class="col-pill">{sanitize_col_name(c)} ({str(active_df[c].dtype)})</span>'
                pills_html += '</div>'
                st.markdown(pills_html, unsafe_allow_html=True)

                st.markdown('<div class="section-label">Dataset Preview</div>', unsafe_allow_html=True)
                
                show_all_rows = st.checkbox("Show all records", value=st.session_state.show_all_data)
                st.session_state.show_all_data = show_all_rows
                
                preview_rows = active_df if show_all_rows else active_df.head(15)
                st.dataframe(preview_rows, use_container_width=True)
            
            with tab_analysis:"""

content = content.replace(old_preview, new_preview)

# Now we need to indent everything from `st.markdown('<div class="section-label">AI Conversation & Command Centre</div>'`
# down to the end of the `if st.session_state.df is not None:` block, except the export stuff which goes in tab_export.

lines = content.split('\\n')
in_analysis = False
in_export = False
new_lines = []

for line in lines:
    if line.strip() == "st.markdown('<div class=\"section-label\">AI Conversation & Command Centre</div>', unsafe_allow_html=True)":
        in_analysis = True
    
    if line.strip() == "st.markdown('<div class=\"section-label\">Export Data</div>', unsafe_allow_html=True)":
        in_analysis = False
        in_export = True
        new_lines.append("            with tab_export:")
        new_lines.append("    " + line)
        continue
        
    if line.strip() == "else:":
        if in_analysis or in_export:
            # End of the big if block
            in_export = False
            in_analysis = False
        
    if in_analysis or in_export:
        if line.strip():  # Add indentation
            new_lines.append("    " + line)
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

content = '\\n'.join(new_lines)

# Also let's add the Export Code and Export Chat features in tab_export
old_export_section = """                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name="nexus_analyst_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )"""

new_export_section = """                st.download_button(
                    label="📥 Download Excel File",
                    data=excel_data,
                    file_name="nexus_analyst_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown('<div class="section-label">Export Reports</div>', unsafe_allow_html=True)
                col_py, col_chat = st.columns(2)
                
                with col_py:
                    code_blocks = [m['content'] for m in st.session_state.chat_history if m['role'] == 'assistant' and '```python' in m['content']]
                    compiled_code = "# Nexus AI Auto-Generated Code\\n\\nimport pandas as pd\\nimport matplotlib.pyplot as plt\\n\\n"
                    for block in code_blocks:
                        import re
                        m = re.search(r"```python\\s*(.*?)\\s*```", block, re.DOTALL)
                        if m:
                            compiled_code += m.group(1) + "\\n\\n"
                    
                    st.download_button(
                        label="📜 Download Python Code (.py)",
                        data=compiled_code.encode('utf-8'),
                        file_name="nexus_analysis_script.py",
                        mime="text/plain",
                        use_container_width=True
                    )
                    
                with col_chat:
                    chat_report = "# Nexus AI Analysis Report\\n\\n"
                    for msg in st.session_state.chat_history:
                        role = "User Request:" if msg['role'] == 'user' else "Nexus AI:"
                        chat_report += f"### {role}\\n{msg['content']}\\n\\n---\\n\\n"
                        
                    st.download_button(
                        label="📝 Download Chat History (.md)",
                        data=chat_report.encode('utf-8'),
                        file_name="nexus_chat_report.md",
                        mime="text/markdown",
                        use_container_width=True
                    )"""

content = content.replace(old_export_section, new_export_section)

with open("Home.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Success")
