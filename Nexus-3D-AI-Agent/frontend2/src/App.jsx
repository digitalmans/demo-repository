import React, { useState, useRef, useEffect } from 'react';
import Web3DScene from './components/Web3DScene';
import './index.css';

// SVG Icons
const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17 8 12 3 7 8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
);

const WandIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}>
    <path d="M15 4V2"></path><path d="M15 16v-2"></path><path d="M8 9h2"></path><path d="M20 9h2"></path><path d="M17.8 11.8L19 13"></path><path d="M15 9h.01"></path><path d="M17.8 6.2L19 5"></path><path d="M3 21l9-9"></path><path d="M12.2 6.2L11 5"></path>
  </svg>
);

const MicIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}>
    <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z"></path>
    <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
    <line x1="12" y1="19" x2="12" y2="22"></line>
  </svg>
);

const SettingsIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}>
    <circle cx="12" cy="12" r="3"></circle>
    <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
  </svg>
);

const ChatIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{marginRight: '8px'}}>
    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
  </svg>
);

function App() {
  const [unityPath, setUnityPath] = useState(localStorage.getItem('unityPath') || 'C:\\Users\\Asus\\chaoliu2');
  const [blenderPath, setBlenderPath] = useState(localStorage.getItem('blenderPath') || 'D:\\360安全浏览器下载\\Blender 5.1\\blender.exe');
  const [prompt, setPrompt] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, running, success, error
  const [logs, setLogs] = useState([]);
  const [ws, setWs] = useState(null);
  
  // 3D Scene State
  const [backgroundPath, setBackgroundPath] = useState(null);
  const [avatars, setAvatars] = useState([]);
  const [showGrid, setShowGrid] = useState(true);
  const [showControls, setShowControls] = useState(true);
  const [controlTarget, setControlTarget] = useState('avatar'); // 'avatar' or 'scene'
  const [manualOffset, setManualOffset] = useState({ x: 0, y: 0, z: 0 }); // Avatar offset
  const [sceneOffset, setSceneOffset] = useState({ x: 0, y: 0, z: 0 }); // Scene offset
  const [manualRotation, setManualRotation] = useState({ x: 0, y: 0, z: 0 }); // Avatar rotation
  const [sceneRotation, setSceneRotation] = useState({ x: 0, y: 0, z: 0 }); // Scene rotation
  const [controlPos, setControlPos] = useState({ x: 0, y: 0 });
  const [isDraggingControl, setIsDraggingControl] = useState(false);
  const [isChatExpanded, setIsChatExpanded] = useState(false);
  const dragRel = useRef({ x: 0, y: 0 });
  
  const fileInputRef = useRef(null);
  const logsEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const avatarStatesRef = useRef({});
  const sceneObjectsRef = useRef({});

  useEffect(() => {
    localStorage.setItem('unityPath', unityPath);
    localStorage.setItem('blenderPath', blenderPath);
  }, [unityPath, blenderPath]);

  // WebSocket Connection
  useEffect(() => {
    const connectWs = () => {
      const socket = new WebSocket('ws://127.0.0.1:8765');
      socket.onopen = () => addLog('🟢 Connected to AI Interactive Server.');
      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          // Backend might return a single action or an array of actions
          const actions = Array.isArray(payload) ? payload : [payload];
          
          actions.forEach(data => {
            if (data.action === "load_scene") {
              addLog(`🌅 [AI] Setting background scene...`);
              setBackgroundPath(data.path);
            } else if (data.action === "load_avatar") {
              addLog(`🏃‍♂️ [AI] Avatar loaded!`);
              setAvatars(prev => [...prev, { path: data.path, positionX: prev.length * 2 }]);
            } else if (data.action === "move_to") {
              addLog(`🤖 [AI] ${data.reply || "Moving"} (目标: ${data.destination})`);
              setAvatars(prev => prev.map((av, idx) => {
                if (!data.target || data.target === `Avatar ${idx + 1}`) {
                   return { ...av, destination: data.destination, trigger: 'Walk', audioBase64: data.audio_base64, dynamicCode: null };
                }
                return av;
              }));
            } else if (data.action === "dynamic_code") {
              addLog(`🤖 [AI] ${data.reply} (正在注入动态代码...)`);
              setAvatars(prev => prev.map((av, idx) => {
                if (!data.target || data.target === `Avatar ${idx + 1}`) {
                   return { ...av, dynamicCode: data.code, audioBase64: data.audio_base64, trigger: data.trigger || 'Idle', destination: null };
                }
                return av;
              }));
            } else if (data.action === "chat") {
              addLog(`🤖 [AI] ${data.reply} (动作触发: ${data.trigger})`);
              setAvatars(prev => prev.map((av, idx) => {
                if (!data.target || data.target === `Avatar ${idx + 1}`) {
                  return { ...av, trigger: data.trigger, audioBase64: data.audio_base64, dynamicCode: null, destination: null };
                }
                return av;
              }));
            } else {
               addLog(`🤖 [AI] ${data.reply}`);
            }
          });
        } catch (e) {
          addLog(`🤖 [AI] ${event.data}`);
        }
      };
      socket.onerror = () => addLog('🔴 Connection error to AI Server. Is Python script running?');
      socket.onclose = () => {
        addLog('🟡 Disconnected from AI Server.');
      };
      setWs(socket);
      return socket;
    };
    
    const socket = connectWs();

    // Setup MediaRecorder for custom STT Backend
    navigator.mediaDevices.getUserMedia({ audio: true }).then(stream => {
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        audioChunksRef.current = [];
        
        addLog(`🎙️ [Voice] 录音完成，正在发送给阿里云 DashScope 识别...`);
        
        const formData = new FormData();
        formData.append("file", audioBlob, "voice.webm");

        try {
          const response = await fetch("http://127.0.0.1:8000/api/v1/transcribe", {
            method: "POST",
            body: formData,
          });
          const data = await response.json();
          if (response.status !== 200) {
             addLog(`🔴 [Voice Error] 服务器返回错误: ${response.status} ${JSON.stringify(data)}`);
          } else if (data.error) {
             addLog(`🔴 [Voice Error] 识别失败: ${data.error}`);
          } else if (data.text !== undefined) {
             if (data.text.trim() === '') {
                 addLog(`🟡 [Voice] 录音已处理，但未识别到任何有效语音`);
             } else {
                 setChatInput(prev => prev + data.text);
                 addLog(`🎙️ [Voice Success] 识别结果已填入文本框: ${data.text}`);
             }
          } else {
             addLog(`🔴 [Voice Error] 未知响应格式: ${JSON.stringify(data)}`);
          }
        } catch (err) {
          addLog(`🔴 [Voice Error] 网络请求失败，请确保后台 speech_provider.py 运行在 8000 端口`);
        }
      };
    }).catch(err => {
      addLog(`🔴 [Mic Error] 无法访问麦克风权限: ${err.message}`);
    });

    return () => {
      if(socket) socket.close();
    };
  }, []);

  // Drag logic for control panel
  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDraggingControl) return;
      const newX = e.clientX - dragRel.current.x;
      const newY = e.clientY - dragRel.current.y;
      setControlPos({ x: newX, y: newY });
    };
    const handleMouseUp = () => setIsDraggingControl(false);

    if (isDraggingControl) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    }
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDraggingControl]);

  const toggleRecording = () => {
    if (!mediaRecorderRef.current) {
      alert("Microphone not accessible. Please allow microphone permissions.");
      return;
    }
    
    if (isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      audioChunksRef.current = [];
      mediaRecorderRef.current.start();
      setIsRecording(true);
      addLog(`🎙️ [Voice] 正在录音... (点击停止以发送)`);
    }
  };

  const addLog = (msg) => {
    setLogs(prev => [...prev, { time: new Date().toLocaleTimeString(), msg }]);
  };

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleFileDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      handleFileSelection(droppedFile);
    }
  };

  const handleFileSelection = (selectedFile) => {
    const ext = selectedFile.name.split('.').pop().toLowerCase();
    if (['obj', '3mf', 'glb', 'gltf', 'fbx'].includes(ext)) {
      setFile(selectedFile);
      setPrompt(''); 
      const objectUrl = URL.createObjectURL(selectedFile);
      setAvatars(prev => [...prev, { path: objectUrl, positionX: prev.length * 2 }]);
      addLog(`[Local] Loaded ${selectedFile.name} into Web3D Scene`);
    } else {
      alert('Only .obj, .3mf, .glb, .gltf, .fbx files are supported.');
    }
  };

  const simulateExecution = () => {
    if (!prompt && !file) {
      alert('Please enter a prompt or upload a model file.');
      return;
    }
    
    setStatus('running');
    addLog('System Initialized.');
    
    let step = 0;
    const interval = setInterval(() => {
      step++;
      if (file && step === 1) {
        addLog(`=== Step 1: Using Local Model: ${file.name} ===`);
      } else if (!file) {
        if (step === 1) {
          addLog(`=== Step 1: AI Generates 2D Image (Pollinations) ===`);
          addLog(`Prompt: "${prompt}"`);
        } else if (step === 2) {
          addLog(`=== Step 2: 2D Image to 3D Model (Tripo3D) ===`);
          addLog(`Extracting meshes and generating textures...`);
        }
      }
      
      const offset = file ? 1 : 2; 

      if (step === offset + 1) {
        addLog(`=== Step 3: Format Conversion & Rigging ===`);
        addLog(`Converting format to FBX and auto-rigging skeleton...`);
      } else if (step === offset + 2) {
        addLog(`=== Step 4: Import to Unity & AI Scene ===`);
        addLog(`Model copied to: ${unityPath}\\Assets\\Models\\AutoGenerated\\temp.fbx`);
        addLog(`👉 Please go to Unity and click "Nexus 3D -> 一键自动配置数字人" to finish setup!`);
      } else if (step === offset + 3) {
        addLog(`=== Step 5 & 6: Avatar Ready! ===`);
        addLog(`Brain (DeepSeek) & Voice (GPT-SoVITS) linked.`);
        addLog(`=== Pipeline Completed Successfully ===`);
        setStatus('success');
        clearInterval(interval);
      }
    }, 1500);
  };

  const handleChatSubmit = (e) => {
    e.preventDefault();
    if (!chatInput.trim() || !ws || ws.readyState !== WebSocket.OPEN) {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert("Not connected to AI Server. Please ensure Python server is running.");
      }
      return;
    }
    addLog(`👤 [You] ${chatInput}`);
    ws.send(JSON.stringify({ 
       text: chatInput,
       sceneState: { avatars: avatarStatesRef.current, objects: sceneObjectsRef.current }
    }));
    setChatInput('');
  };

  const handleReachDestination = (idx) => {
      setAvatars(prev => prev.map((av, i) => {
          if (i === idx) {
              return { ...av, destination: null, trigger: 'Idle' };
          }
          return av;
      }));
  };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <header className="app-header">
        <h1 className="app-title">Nexus 3D</h1>
        <p className="app-subtitle">AI Generation & Unity Automation Agent</p>
      </header>

      <div className="grid-2">
        <div style={{display: 'flex', flexDirection: 'column', gap: '2rem', overflowY: 'auto', paddingRight: '10px', minHeight: 0}}>
          
          <div className="glass-panel" style={{display: 'flex', flexDirection: 'column'}}>
            <h2 style={{marginBottom: '1rem', display: 'flex', alignItems: 'center'}}>
              <WandIcon /> Create Asset
            </h2>
            
            <p style={{ color: '#fbbf24', fontSize: '0.85rem', marginBottom: '1.5rem', backgroundColor: 'rgba(251, 191, 36, 0.1)', padding: '0.75rem', borderRadius: '8px' }}>
              说明：放入 Unity 的最好是人物模型，否则不保证一定能动。
            </p>

            <div style={{display: 'flex', gap: '10px', marginBottom: '1.5rem'}}>
              <button 
                className="btn" 
                style={{flex: 1, background: 'transparent', border: '1px solid var(--accent-color)', color: 'var(--text-primary)'}}
                onClick={() => setShowGrid(!showGrid)}
              >
                {showGrid ? '🙈 Hide Grid' : '👁️ Show Grid'}
              </button>
              <button 
                className="btn" 
                style={{flex: 1, background: 'transparent', border: '1px solid var(--accent-color)', color: 'var(--text-primary)'}}
                onClick={() => setShowControls(!showControls)}
              >
                {showControls ? '🎮 Hide D-Pad' : '🎮 Show D-Pad'}
              </button>
            </div>

            <div 
              className={`drop-zone ${file ? 'active' : ''}`}
              onDragOver={(e) => e.preventDefault()}
              onDrop={handleFileDrop}
              onClick={() => fileInputRef.current.click()}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                style={{display: 'none'}} 
                accept=".obj,.3mf,.glb,.gltf"
                onChange={(e) => handleFileSelection(e.target.files[0])}
              />
              <div className="drop-icon"><UploadIcon /></div>
              {file ? (
                <h3 style={{color: 'var(--accent-color)'}}>{file.name}</h3>
              ) : (
                <>
                  <h3>Drop local model here</h3>
                  <p style={{color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.5rem'}}>Supports .OBJ, .3MF, .GLB</p>
                </>
              )}
            </div>

            <div style={{textAlign: 'center', margin: '1rem 0', color: 'var(--text-secondary)', fontWeight: 'bold'}}>— OR —</div>

            <div className="input-group">
              <label className="input-label">AI Generation Prompt</label>
              <textarea 
                className="input-field" 
                placeholder="e.g. A low poly wooden crate with iron bindings..."
                rows="2"
                value={prompt}
                onChange={(e) => {setPrompt(e.target.value); setFile(null);}}
                disabled={status === 'running'}
                style={{resize: 'none'}}
              />
            </div>

            <button 
              className="btn" 
              style={{marginTop: 'auto', width: '100%'}}
              onClick={simulateExecution}
              disabled={status === 'running'}
            >
              {status === 'running' ? 'Processing Workflow...' : 'Run Pipeline'}
            </button>
          </div>

          <div className="glass-panel" style={{display: 'flex', flexDirection: 'column'}}>
            <h2 style={{marginBottom: '1rem', display: 'flex', alignItems: 'center'}}>
              <ChatIcon /> AI Voice Commands & Chat
            </h2>
            <form onSubmit={handleChatSubmit} style={{display: 'flex', gap: '10px'}}>
              <button 
                type="button"
                className={`btn ${isRecording ? 'recording' : ''}`} 
                style={{padding: '0.75rem', backgroundColor: isRecording ? '#ef4444' : '#3b82f6', minWidth: '50px'}}
                onClick={toggleRecording}
                title="Hold to speak"
              >
                <MicIcon />
              </button>
              <input 
                type="text" 
                className="input-field" 
                style={{marginBottom: 0, flex: 1, cursor: 'text'}}
                placeholder="e.g. 生成一个赛博朋克场景 / 1号跟我挥挥手"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
              />
              <button 
                type="button" 
                className="btn" 
                style={{padding: '0.75rem', background: 'transparent', border: '1px solid var(--accent-color)'}}
                onClick={() => setIsChatExpanded(true)}
                title="Expand Input"
              >
                ⛶
              </button>
              <button type="submit" className="btn" style={{padding: '0.75rem 1.5rem'}}>
                Send
              </button>
            </form>
          </div>

        </div>

        <div style={{display: 'flex', flexDirection: 'column', gap: '1rem', flex: 2}}>
          
          <div className="glass-panel" style={{flex: 1, padding: '10px', position: 'relative', overflow: 'hidden'}}>
            <Web3DScene 
              backgroundPath={backgroundPath} 
              avatars={avatars} 
              showGrid={showGrid} 
              manualOffset={manualOffset} 
              sceneOffset={sceneOffset} 
              manualRotation={manualRotation} 
              sceneRotation={sceneRotation} 
              onReachDestination={handleReachDestination}
              avatarStatesRef={avatarStatesRef}
              sceneObjectsRef={sceneObjectsRef}
            />
            
            {showControls && (
              <div 
                onMouseDown={(e) => {
                  if (e.target.tagName.toLowerCase() === 'button') return;
                  setIsDraggingControl(true);
                  dragRel.current = {
                    x: e.clientX - controlPos.x,
                    y: e.clientY - controlPos.y
                  };
                }}
                style={{
                  position: 'absolute',
                  right: controlPos.x === 0 && controlPos.y === 0 ? '20px' : 'auto',
                  bottom: controlPos.x === 0 && controlPos.y === 0 ? '180px' : 'auto',
                  left: controlPos.x !== 0 || controlPos.y !== 0 ? 0 : 'auto',
                  top: controlPos.x !== 0 || controlPos.y !== 0 ? 0 : 'auto',
                  transform: controlPos.x !== 0 || controlPos.y !== 0 ? `translate(${controlPos.x}px, ${controlPos.y}px)` : 'none',
                  background: 'rgba(255,255,255,0.1)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: '12px',
                  padding: '10px',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '5px',
                  border: '1px solid rgba(255,255,255,0.2)',
                  cursor: isDraggingControl ? 'grabbing' : 'grab',
                  userSelect: 'none'
                }}
              >
                 <div style={{color: 'white', fontSize: '12px', marginBottom: '5px', fontWeight: 'bold'}}>手动控制台 (拖动此处)</div>
                 
                 <div style={{display: 'flex', gap: '5px', marginBottom: '5px', background: 'rgba(0,0,0,0.3)', padding: '3px', borderRadius: '8px'}}>
                    <button 
                      style={{padding: '3px 8px', fontSize: '11px', borderRadius: '5px', border: 'none', background: controlTarget === 'avatar' ? 'var(--accent-color)' : 'transparent', color: 'white', cursor: 'pointer'}}
                      onClick={() => setControlTarget('avatar')}
                    >控制数字人</button>
                    <button 
                      style={{padding: '3px 8px', fontSize: '11px', borderRadius: '5px', border: 'none', background: controlTarget === 'scene' ? 'var(--accent-color)' : 'transparent', color: 'white', cursor: 'pointer'}}
                      onClick={() => setControlTarget('scene')}
                    >控制场景(视角)</button>
                 </div>

                 <div style={{display: 'flex', gap: '5px'}}>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, y: p.y + 0.5})) : setSceneOffset(p => ({...p, y: p.y - 0.5}))}>升(Y+)</button>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, z: p.z - 0.5})) : setSceneOffset(p => ({...p, z: p.z + 0.5}))}>前(Z-)</button>
                 </div>
                 <div style={{display: 'flex', gap: '5px'}}>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, x: p.x - 0.5})) : setSceneOffset(p => ({...p, x: p.x + 0.5}))}>左(X-)</button>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => {
                        if (controlTarget === 'avatar') {
                            setManualOffset({x:0, y:0, z:0});
                            setManualRotation({x:0, y:0, z:0});
                        } else {
                            setSceneOffset({x:0, y:0, z:0});
                            setSceneRotation({x:0, y:0, z:0});
                        }
                    }}>重置</button>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, x: p.x + 0.5})) : setSceneOffset(p => ({...p, x: p.x - 0.5}))}>右(X+)</button>
                 </div>
                 <div style={{display: 'flex', gap: '5px'}}>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, y: p.y - 0.5})) : setSceneOffset(p => ({...p, y: p.y + 0.5}))}>降(Y-)</button>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer'}} onClick={() => controlTarget === 'avatar' ? setManualOffset(p => ({...p, z: p.z + 0.5})) : setSceneOffset(p => ({...p, z: p.z - 0.5}))}>后(Z+)</button>
                 </div>
                 
                 <div style={{display: 'flex', gap: '5px'}}>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer', background: 'var(--bg-card)'}} onClick={() => controlTarget === 'avatar' ? setManualRotation(p => ({...p, y: p.y + Math.PI/8})) : setSceneRotation(p => ({...p, y: p.y + Math.PI/8}))}>↺ 左转</button>
                    <button className="btn" style={{padding: '5px 10px', minWidth: '40px', cursor: 'pointer', background: 'var(--bg-card)'}} onClick={() => controlTarget === 'avatar' ? setManualRotation(p => ({...p, y: p.y - Math.PI/8})) : setSceneRotation(p => ({...p, y: p.y - Math.PI/8}))}>右转 ↻</button>
                 </div>
              </div>
            )}

            <div style={{
              position: 'absolute',
              bottom: '10px',
              left: '10px',
              right: '10px',
              height: '150px',
              background: 'rgba(0,0,0,0.7)', 
              borderRadius: '8px', 
              padding: '1rem',
              fontFamily: 'monospace',
              fontSize: '0.85rem',
              color: '#10b981',
              overflowY: 'auto',
              pointerEvents: 'none'
            }}>
              {logs.length === 0 && <span style={{color: 'var(--text-secondary)'}}>Waiting for AI commands...</span>}
              {logs.map((log, i) => (
                <div key={i} style={{marginBottom: '0.2rem'}}>
                  <span style={{opacity: 0.5, marginRight: '0.5rem'}}>[{log.time}]</span>
                  {log.msg}
                </div>
              ))}
              {status === 'running' && (
                <div className="animate-pulse" style={{marginTop: '0.5rem'}}>_</div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>
      </div>

      {isChatExpanded && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, 
          background: 'rgba(0,0,0,0.7)', zIndex: 9999,
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <div className="glass-panel" style={{ width: '600px', maxWidth: '90%', display: 'flex', flexDirection: 'column', gap: '1rem', padding: '2rem' }}>
            <h3 style={{color: 'white', display: 'flex', justifyContent: 'space-between'}}>
              <span>✍️ 编辑长指令</span>
              <button onClick={() => setIsChatExpanded(false)} style={{background:'transparent', border:'none', color:'white', cursor:'pointer'}}>✖</button>
            </h3>
            <textarea 
              autoFocus
              className="input-field" 
              style={{ minHeight: '200px', resize: 'vertical', fontSize: '1.1rem' }}
              value={chatInput}
              onChange={e => setChatInput(e.target.value)}
              placeholder="在这里输入复杂的指令或代码..."
            />
            <div style={{display: 'flex', gap: '10px', justifyContent: 'flex-end'}}>
              <button className="btn" style={{background: 'transparent', border: '1px solid gray'}} onClick={() => setIsChatExpanded(false)}>取消</button>
              <button className="btn" onClick={(e) => {
                setIsChatExpanded(false);
                handleChatSubmit(e);
              }}>发送 (Send)</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
