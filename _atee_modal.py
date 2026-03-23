MODAL_HTML = r"""
    <!-- ATEE: Adaptive Task Execution Engine -->
    <div id="atee-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.85);z-index:3000;flex-direction:column;">

      <!-- ATEE Header Bar -->
      <div style="background:var(--surface2);border-bottom:1px solid var(--border);padding:.625rem 1.25rem;display:flex;align-items:center;gap:1rem;flex-shrink:0;">
        <div style="display:flex;align-items:center;gap:.625rem;flex:1;min-width:0;">
          <div style="width:8px;height:8px;border-radius:50%;background:#22c55e;" id="atee-status-dot"></div>
          <div style="font-size:.6875rem;color:#f97316;font-weight:700;text-transform:uppercase;letter-spacing:.06em;">Task Engine</div>
          <div style="font-size:.875rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" id="atee-header-title">—</div>
        </div>
        <!-- Progress bar -->
        <div style="flex:1;max-width:200px;background:var(--surface4);border-radius:10px;height:6px;overflow:hidden;">
          <div id="atee-progress-bar" style="height:100%;background:linear-gradient(90deg,#f97316,#f59e0b);border-radius:10px;width:0%;transition:width .4s ease;"></div>
        </div>
        <div style="font-size:.75rem;color:var(--text3);" id="atee-progress-label">0%</div>
        <!-- Mode toggle -->
        <div style="display:flex;gap:.25rem;background:var(--surface3);border-radius:8px;padding:.2rem;">
          <button id="atee-mode-manual" onclick="ateeSetMode('manual')" style="font-size:.6875rem;padding:.25rem .625rem;border-radius:6px;border:none;cursor:pointer;background:#f97316;color:#fff;font-weight:600;">Manual</button>
          <button id="atee-mode-auto" onclick="ateeSetMode('auto')" style="font-size:.6875rem;padding:.25rem .625rem;border-radius:6px;border:none;cursor:pointer;background:transparent;color:var(--text3);font-weight:600;">Autopilot</button>
        </div>
        <button onclick="closeATEE()" style="background:none;border:none;color:var(--text3);cursor:pointer;font-size:1.1rem;padding:.25rem;">✕</button>
      </div>

      <!-- ATEE Body: 3-column layout -->
      <div style="display:flex;flex:1;overflow:hidden;min-height:0;">

        <!-- LEFT: Steps Panel -->
        <div style="width:220px;flex-shrink:0;background:var(--surface2);border-right:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;">
          <div style="padding:.75rem 1rem;border-bottom:1px solid var(--border);font-size:.75rem;font-weight:700;color:var(--text3);text-transform:uppercase;letter-spacing:.05em;">Steps</div>
          <div style="overflow-y:auto;flex:1;padding:.5rem;" id="atee-steps-list">
            <div style="text-align:center;padding:1.5rem .5rem;color:var(--text3);font-size:.75rem;">Generate plan to see steps</div>
          </div>
          <div style="padding:.625rem;border-top:1px solid var(--border);">
            <button class="btn btn-primary btn-sm" style="width:100%;font-size:.75rem;" onclick="ateeGeneratePlan()">🧠 Generate Plan</button>
          </div>
        </div>

        <!-- CENTER: Tool Canvas -->
        <div style="flex:1;display:flex;flex-direction:column;overflow:hidden;min-width:0;">

          <!-- Tool Toolbar -->
          <div style="background:var(--surface3);border-bottom:1px solid var(--border);padding:.375rem .75rem;display:flex;align-items:center;gap:.375rem;flex-shrink:0;overflow-x:auto;">
            <span style="font-size:.6875rem;color:var(--text3);white-space:nowrap;">Active Tool:</span>
            <span id="atee-active-tool-label" style="font-size:.75rem;font-weight:700;color:#f97316;white-space:nowrap;">None</span>
            <div style="margin-left:auto;display:flex;gap:.25rem;">
              <button onclick="ateeSwitchTool('editor')" class="atee-tool-btn" title="Editor" style="background:var(--surface4);border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">📝 Editor</button>
              <button onclick="ateeSwitchTool('search')" class="atee-tool-btn" title="Research" style="background:var(--surface4);border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">🔍 Research</button>
              <button onclick="ateeSwitchTool('sheets')" class="atee-tool-btn" title="Sheets" style="background:var(--surface4);border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">📊 Sheets</button>
              <button onclick="ateeSwitchTool('slides')" class="atee-tool-btn" title="Slides" style="background:var(--surface4);border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">🎞 Slides</button>
              <button onclick="ateeSwitchTool('notes')" class="atee-tool-btn" title="Notes" style="background:var(--surface4);border:1px solid var(--border);border-radius:6px;padding:.25rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">🗒 Notes</button>
            </div>
          </div>

          <!-- Tool Canvas Area -->
          <div style="flex:1;overflow:hidden;position:relative;" id="atee-canvas-wrap">

            <!-- Editor Tool -->
            <div id="atee-tool-editor" class="atee-tool" style="display:none;height:100%;flex-direction:column;">
              <div style="padding:.5rem .75rem;background:var(--surface3);border-bottom:1px solid var(--border);display:flex;gap:.375rem;flex-shrink:0;flex-wrap:wrap;">
                <button onclick="ateeEditorFormat('bold')" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);font-weight:700;">B</button>
                <button onclick="ateeEditorFormat('italic')" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);font-style:italic;">I</button>
                <button onclick="ateeEditorFormat('insertUnorderedList')" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">• List</button>
                <button onclick="ateeEditorFormat('insertOrderedList')" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">1. List</button>
                <button onclick="ateeAIImproveEditor()" style="background:#f97316;border:none;border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:#fff;margin-left:auto;">✨ AI Improve</button>
                <button onclick="ateeSaveToolOutput('editor')" style="background:var(--surface4);border:1px solid var(--border);border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:var(--text);">💾 Save</button>
              </div>
              <div id="atee-editor-content" contenteditable="true" style="flex:1;padding:1rem;font-size:.875rem;line-height:1.7;color:var(--text);overflow-y:auto;outline:none;background:var(--surface2);" placeholder="Start writing here..."></div>
            </div>

            <!-- Research Tool -->
            <div id="atee-tool-search" class="atee-tool" style="display:none;height:100%;flex-direction:column;">
              <div style="padding:.625rem .75rem;background:var(--surface3);border-bottom:1px solid var(--border);display:flex;gap:.375rem;flex-shrink:0;">
                <input id="atee-search-input" type="text" placeholder="Search for research..." style="flex:1;background:var(--surface2);border:1px solid var(--border);border-radius:6px;padding:.375rem .625rem;font-size:.8125rem;color:var(--text);" onkeydown="if(event.key==='Enter')ateeDoSearch()">
                <button onclick="ateeDoSearch()" class="btn btn-primary btn-sm">Search</button>
                <button onclick="ateeAIResearch()" class="btn btn-ghost btn-sm" style="color:#f97316;">🤖 AI Research</button>
              </div>
              <div id="atee-search-results" style="flex:1;overflow-y:auto;padding:.75rem;font-size:.8125rem;color:var(--text2);">
                <div style="text-align:center;padding:2rem;color:var(--text3);">Enter a query to research your task topic.</div>
              </div>
            </div>

            <!-- Sheets Tool -->
            <div id="atee-tool-sheets" class="atee-tool" style="display:none;height:100%;flex-direction:column;">
              <div style="padding:.5rem .75rem;background:var(--surface3);border-bottom:1px solid var(--border);display:flex;gap:.375rem;flex-shrink:0;">
                <button onclick="ateeAddSheetRow()" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">+ Row</button>
                <button onclick="ateeAddSheetCol()" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">+ Col</button>
                <button onclick="ateeAIFillSheet()" style="background:#f97316;border:none;border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:#fff;margin-left:auto;">🤖 AI Fill</button>
                <button onclick="ateeSaveToolOutput('sheets')" style="background:var(--surface4);border:1px solid var(--border);border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:var(--text);">💾 Save</button>
              </div>
              <div style="flex:1;overflow:auto;padding:.5rem;">
                <table id="atee-sheet-table" style="border-collapse:collapse;font-size:.8125rem;min-width:100%;">
                  <tbody id="atee-sheet-body"></tbody>
                </table>
              </div>
            </div>

            <!-- Slides Tool -->
            <div id="atee-tool-slides" class="atee-tool" style="display:none;height:100%;flex-direction:column;">
              <div style="padding:.5rem .75rem;background:var(--surface3);border-bottom:1px solid var(--border);display:flex;gap:.375rem;flex-shrink:0;align-items:center;">
                <button onclick="ateeAddSlide()" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">+ Slide</button>
                <span style="font-size:.75rem;color:var(--text3);" id="atee-slide-counter">Slide 1 / 1</span>
                <button onclick="ateePrevSlide()" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">◀</button>
                <button onclick="ateeNextSlide()" style="background:none;border:1px solid var(--border);border-radius:4px;padding:.2rem .5rem;font-size:.75rem;cursor:pointer;color:var(--text);">▶</button>
                <button onclick="ateeAIGenerateSlides()" style="background:#f97316;border:none;border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:#fff;margin-left:auto;">🤖 AI Generate</button>
                <button onclick="ateeSaveToolOutput('slides')" style="background:var(--surface4);border:1px solid var(--border);border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:var(--text);">💾 Save</button>
              </div>
              <div style="flex:1;overflow:hidden;display:flex;gap:.5rem;padding:.5rem;">
                <!-- Slide thumbnails -->
                <div id="atee-slide-thumbs" style="width:100px;overflow-y:auto;display:flex;flex-direction:column;gap:.375rem;flex-shrink:0;"></div>
                <!-- Active slide -->
                <div style="flex:1;background:#1a1a2e;border-radius:8px;display:flex;align-items:center;justify-content:center;overflow:hidden;">
                  <div id="atee-slide-active" contenteditable="true" style="width:100%;max-width:560px;aspect-ratio:16/9;background:linear-gradient(135deg,#1e1b4b,#312e81);border-radius:8px;padding:2rem;display:flex;flex-direction:column;justify-content:center;color:#fff;outline:none;">
                    <div style="font-size:1.25rem;font-weight:700;margin-bottom:.5rem;" id="atee-slide-title">Slide Title</div>
                    <div style="font-size:.875rem;opacity:.8;line-height:1.6;" id="atee-slide-body">Click to edit content...</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Notes Tool -->
            <div id="atee-tool-notes" class="atee-tool" style="display:none;height:100%;flex-direction:column;">
              <div style="padding:.5rem .75rem;background:var(--surface3);border-bottom:1px solid var(--border);display:flex;gap:.375rem;flex-shrink:0;">
                <span style="font-size:.75rem;font-weight:600;color:var(--text2);">Quick Notes</span>
                <button onclick="ateeSaveToolOutput('notes')" style="background:var(--surface4);border:1px solid var(--border);border-radius:4px;padding:.2rem .625rem;font-size:.75rem;cursor:pointer;color:var(--text);margin-left:auto;">💾 Save</button>
              </div>
              <textarea id="atee-notes-content" placeholder="Jot down notes, ideas, references..." style="flex:1;background:var(--surface2);border:none;padding:1rem;font-size:.875rem;color:var(--text);resize:none;outline:none;line-height:1.7;"></textarea>
            </div>

          </div>

          <!-- Output Saved Bar -->
          <div id="atee-saved-bar" style="display:none;background:#22c55e22;border-top:1px solid #22c55e44;padding:.375rem .75rem;font-size:.75rem;color:#22c55e;flex-shrink:0;">
            ✓ Output saved to task activity
          </div>

        </div>

        <!-- RIGHT: AI Assistant Panel -->
        <div style="width:260px;flex-shrink:0;background:var(--surface2);border-left:1px solid var(--border);display:flex;flex-direction:column;overflow:hidden;">
          <div style="padding:.75rem 1rem;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:.5rem;flex-shrink:0;">
            <div style="width:28px;height:28px;border-radius:50%;background:linear-gradient(135deg,#7c3aed,#f97316);display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;color:#fff;flex-shrink:0;">AI</div>
            <div>
              <div style="font-size:.75rem;font-weight:700;">Nexa Assistant</div>
              <div style="font-size:.625rem;color:#22c55e;">● Active</div>
            </div>
          </div>
          <!-- AI Messages -->
          <div id="atee-ai-msgs" style="flex:1;overflow-y:auto;padding:.75rem;display:flex;flex-direction:column;gap:.625rem;">
            <div class="atee-ai-bubble" style="background:var(--surface3);border:1px solid var(--border);border-radius:10px;border-top-left-radius:2px;padding:.625rem .75rem;font-size:.8125rem;color:var(--text2);line-height:1.5;">
              👋 Open a task and click <strong>Start Task</strong> to begin. I'll guide you through every step.
            </div>
          </div>
          <!-- AI Suggestions -->
          <div id="atee-suggestions" style="padding:.5rem;border-top:1px solid var(--border);display:flex;flex-direction:column;gap:.25rem;flex-shrink:0;"></div>
          <!-- AI Input -->
          <div style="padding:.5rem;border-top:1px solid var(--border);flex-shrink:0;">
            <div style="display:flex;gap:.375rem;">
              <input id="atee-ai-input" type="text" placeholder="Ask AI anything..." style="flex:1;background:var(--surface3);border:1px solid var(--border);border-radius:6px;padding:.375rem .5rem;font-size:.75rem;color:var(--text);" onkeydown="if(event.key==='Enter')ateeSendAI()">
              <button onclick="ateeSendAI()" style="background:#f97316;border:none;border-radius:6px;padding:.375rem .625rem;cursor:pointer;color:#fff;font-size:.75rem;">→</button>
            </div>
          </div>
        </div>

      </div>

      <!-- ATEE Footer -->
      <div style="background:var(--surface2);border-top:1px solid var(--border);padding:.625rem 1.25rem;display:flex;align-items:center;gap:.75rem;flex-shrink:0;">
        <div style="font-size:.75rem;color:var(--text3);" id="atee-current-step-label">No active step</div>
        <div style="margin-left:auto;display:flex;gap:.5rem;">
          <button class="btn btn-ghost btn-sm" onclick="ateePrevStep()">◀ Prev</button>
          <button class="btn btn-primary btn-sm" onclick="ateeCompleteStep()" id="atee-complete-btn">✓ Complete Step</button>
          <button class="btn btn-primary btn-sm" onclick="ateeNextStep()">Next ▶</button>
          <button class="btn btn-ghost btn-sm" style="color:#ef4444;" onclick="ateeShowSubmit()">📤 Submit Task</button>
        </div>
      </div>

    </div>

    <!-- ATEE Submit Review Modal -->
    <div id="atee-submit-modal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,.8);z-index:4000;align-items:center;justify-content:center;padding:1rem;">
      <div style="background:var(--surface2);border:1px solid var(--border2);border-radius:14px;width:100%;max-width:600px;max-height:85vh;overflow-y:auto;padding:1.5rem;">
        <div style="font-size:.875rem;font-weight:700;margin-bottom:1rem;">📦 Task Submission Review</div>
        <div id="atee-submit-summary" style="font-size:.8125rem;color:var(--text2);line-height:1.6;margin-bottom:1rem;"></div>
        <div style="font-size:.75rem;font-weight:600;margin-bottom:.5rem;">Final Output</div>
        <textarea id="atee-submit-content" rows="8" style="width:100%;background:var(--surface3);border:1px solid var(--border);border-radius:8px;padding:.75rem;font-size:.8125rem;color:var(--text);resize:vertical;margin-bottom:1rem;"></textarea>
        <div style="display:flex;gap:.5rem;justify-content:flex-end;">
          <button class="btn btn-ghost btn-sm" onclick="document.getElementById('atee-submit-modal').style.display='none'">Cancel</button>
          <button class="btn btn-primary" onclick="ateeSubmitFinal()">✅ Submit Task</button>
        </div>
      </div>
    </div>

"""

with open('community/templates/community/workspace_detail.html', 'r', encoding='utf-8', errors='replace') as f:
    c = f.read()

# Replace the old task-engine-modal + add-to-task-fab with the new ATEE modal
old_start = c.find('<!-- Task Engine Modal -->')
old_end = c.find('<!-- Submit Work Modal -->', old_start)

if old_start != -1 and old_end != -1:
    c = c[:old_start] + MODAL_HTML + '\n    ' + c[old_end:]
    print('ATEE modal inserted, replacing old task engine modal')
else:
    print('Could not find old modal bounds')
    print('old_start:', old_start, 'old_end:', old_end)

with open('community/templates/community/workspace_detail.html', 'w', encoding='utf-8', errors='replace') as f:
    f.write(c)

print('Done. atee-modal in file:', 'atee-modal' in c)
