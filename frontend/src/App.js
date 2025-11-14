import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Spinner } from '@maxhub/max-ui';
import './App.css';

const AnimatedPlaceholder = () => {
  const ideas = ["Подготовиться к стажировке в VK", "Выучить Python для анализа данных", "Написать дипломную работу по нейросетям", "Запустить свой первый пет-проект", "Освоить React и TypeScript за 3 месяца"];
  const [placeholder, setPlaceholder] = useState('');
  const ideaIndex = useRef(0);
  const charIndex = useRef(0);
  const isDeleting = useRef(false);
  const timeoutRef = useRef(null);
  useEffect(() => {
    const type = () => {
      const currentIdea = ideas[ideaIndex.current];
      let newPlaceholder = '';
      let timeout = 150;
      if (isDeleting.current) {
        newPlaceholder = currentIdea.substring(0, charIndex.current - 1);
        charIndex.current--;
        timeout = 75;
      } else {
        newPlaceholder = currentIdea.substring(0, charIndex.current + 1);
        charIndex.current++;
      }
      setPlaceholder(newPlaceholder);
      if (!isDeleting.current && newPlaceholder === currentIdea) {
        isDeleting.current = true;
        timeout = 2000;
      } else if (isDeleting.current && newPlaceholder === '') {
        isDeleting.current = false;
        ideaIndex.current = (ideaIndex.current + 1) % ideas.length;
        timeout = 500;
      }
      timeoutRef.current = setTimeout(type, timeout);
    };
    timeoutRef.current = setTimeout(type, 1000);
    return () => clearTimeout(timeoutRef.current);
  }, []);
  return <div className="animated-placeholder">{placeholder}</div>;
};

const RoadmapNode = ({ step, onToggle, onDecompose, isSubNode = false }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDecomposing, setIsDecomposing] = useState(false);

  const handleDecompose = async (e) => {
    e.stopPropagation();
    setIsDecomposing(true);
    await onDecompose(step.id);
    setIsDecomposing(false);
    setIsExpanded(true);
  };

  const hasChildren = step.children && step.children.length > 0;
  const canDecompose = !hasChildren;
  const nodeClass = isSubNode ? 'sub-step-node' : 'top-level-node';

  return (
    <div className={`step-node ${nodeClass} ${step.is_done ? 'done' : ''}`}>
      <div className="step-header" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="difficulty-dot-wrapper">
          <div className={`difficulty-dot ${step.difficulty}`}></div>
        </div>
        <input type="checkbox" className="roadmap-checkbox" checked={step.is_done} onChange={() => onToggle(step.id)} onClick={(e) => e.stopPropagation()} />
        <span className="step-title">{step.title}</span>
        {canDecompose && (
          <button className="decompose-button" onClick={handleDecompose} disabled={isDecomposing}>
            {isDecomposing ? <Spinner /> : '+'}
          </button>
        )}
        <div className={`step-indicator ${isExpanded ? 'expanded' : ''}`}>{hasChildren || step.description ? '›' : ''}</div>
      </div>
      {isExpanded && (
        <div className="step-content">
          {step.description && <p className="step-description">{step.description}</p>}
          {hasChildren && (
            <div className="children-container">
              {step.children.map(childStep => (
                <RoadmapNode key={childStep.id} step={childStep} onToggle={onToggle} onDecompose={onDecompose} isSubNode={true} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const CreateScreen = ({ onRoadmapCreated, maxUserId, onShowList }) => {
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCreateRoadmap = async () => {
    if (!maxUserId) { setError("ID пользователя не найден."); return; }
    if (!prompt) { setError('Пожалуйста, введите вашу цель'); return; }
    setIsLoading(true);
    setError('');
    try {
      const response = await axios.post('/api/roadmaps', { prompt: prompt, maxUserId: maxUserId });
      onRoadmapCreated(response.data);
    } catch (err) {
      setError('Ошибка на стороне GigaChat. Попробуйте переформулировать цель или повторить попытку.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="create-container">
      <div className="create-header">
        <h1 className="welcome-title">NNAImark</h1>
        <p className="subtitle">Ваш персональный навигатор в достижении целей. Опишите вашу цель - я построю план.</p>
      </div>
      <div className="actions-wrapper">
        <button className="action-button button-secondary" onClick={onShowList}>
          📚 Мои Роадмапы
        </button>
      </div>
      <div className="separator">или создайте новый</div>
      <div className="prompt-wrapper">
        {!prompt && <AnimatedPlaceholder />}
        <textarea
          className={`prompt-input ${!prompt ? 'transparent-bg' : ''}`}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={isLoading}
        />
      </div>
      <div className="button-wrapper">
        <button className="action-button button-primary" onClick={handleCreateRoadmap} disabled={isLoading || !maxUserId}>
          {isLoading ? <Spinner /> : 'Проложить курс'}
        </button>
      </div>
      {error && <p className="error-message">{error}</p>}
    </div>
  );
};

const ListScreen = ({ onSelectRoadmap, onCreateNew, roadmaps, isLoading }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filteredRoadmaps = roadmaps.filter(rm => 
    rm.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="list-container">
      <h1>Мои Роадмапы</h1>
      <div className="search-wrapper">
        <input 
          type="text"
          className="search-input"
          placeholder="Найти роадмап..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>
      {isLoading ? (
        <div className="centered-spinner"><Spinner size="large" /></div>
      ) : (
        <div className="roadmap-list">
          {roadmaps.length > 0 && filteredRoadmaps.length > 0 && (
            filteredRoadmaps.map(rm => (
              <div key={rm.id} className="roadmap-card" onClick={() => onSelectRoadmap(rm.id)}>
                <span className="card-title">{rm.title}</span>
                <span className="card-progress">{rm.progress}</span>
              </div>
            ))
          )}
          {roadmaps.length > 0 && filteredRoadmaps.length === 0 && (
            <p className="empty-list-message">Ничего не найдено по вашему запросу.</p>
          )}
          {roadmaps.length === 0 && (
            <p className="empty-list-message">У вас пока нет созданных планов. Пора это исправить!</p>
          )}
        </div>
      )}
      <div className="button-wrapper">
        <button onClick={onCreateNew} className="action-button button-primary">Создать новый</button>
      </div>
    </div>
  );
};

const RoadmapScreen = ({ roadmap, onBack, onToggle, onDecompose, onDelete }) => (
  <div className="roadmap-container">
    <h1>{roadmap.title}</h1>
    <div className="steps-wrapper">
      {roadmap.steps.map((step) => (
        <RoadmapNode key={step.id} step={step} onToggle={onToggle} onDecompose={onDecompose} />
      ))}
    </div>
    <div className="button-wrapper roadmap-actions">
      <button onClick={onBack} className="action-button button-secondary">Назад к списку</button>
      <button onClick={() => onDelete(roadmap.id)} className="action-button button-danger">Удалить</button>
    </div>
  </div>
);

function App() {
  const [maxUserId, setMaxUserId] = useState(null);
  const [view, setView] = useState('loading');
  const [roadmapList, setRoadmapList] = useState([]);
  const [currentRoadmap, setCurrentRoadmap] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 20;
    const intervalId = setInterval(() => {
      attempts++;
      const WebApp = window.WebApp;
      if (WebApp && WebApp.initDataUnsafe && WebApp.initDataUnsafe.user && WebApp.initDataUnsafe.user.id) {
        clearInterval(intervalId);
        const userId = String(WebApp.initDataUnsafe.user.id);
        setMaxUserId(userId);
        setView('create'); 
        WebApp.ready();
        return;
      }
      if (attempts >= maxAttempts) {
        clearInterval(intervalId);
        if (window.self === window.top) {
            setMaxUserId("DEBUG_USER_12345");
            setView('create');
        } else {
            setError("Ошибка инициализации. Не удалось получить данные от MAX.");
            setIsLoading(false);
        }
      }
    }, 200);
    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {
    if (view === 'list' && maxUserId) {
      setIsLoading(true);
      setError('');
      axios.get(`/api/roadmaps?maxUserId=${maxUserId}`)
        .then(response => { setRoadmapList(response.data); })
        .catch(err => { setError('Не удалось загрузить список роадмапов.'); console.error(err); })
        .finally(() => { setIsLoading(false); });
    } else if (view !== 'loading') {
        setIsLoading(false);
    }
  }, [view, maxUserId]);
  
  const handleSelectRoadmap = (roadmapId) => {
    setIsLoading(true);
    setError('');
    axios.get(`/api/roadmaps/${roadmapId}`)
      .then(response => {
        setCurrentRoadmap(response.data);
        setView('roadmap');
      })
      .catch(err => {
        setError('Не удалось загрузить роадмап.');
        console.error(err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const handleRoadmapCreated = (newRoadmap) => {
    const totalSteps = newRoadmap.steps ? newRoadmap.steps.length : 0;
    setRoadmapList(prevList => [...prevList, {
      id: newRoadmap.id,
      title: newRoadmap.title,
      progress: `0/${totalSteps}` 
    }]);
    setCurrentRoadmap(newRoadmap);
    setView('roadmap');
  };

  const handleBack = () => {
    setCurrentRoadmap(null);
    setView('list');
  };

  const handleDeleteRoadmap = async (roadmapId) => {
    if (window.confirm('Вы уверены, что хотите удалить этот роадмап? Это действие необратимо.')) {
      try {
        await axios.delete(`/api/roadmaps/${roadmapId}`);
        setRoadmapList(prevList => prevList.filter(rm => rm.id !== roadmapId));
        setView('list');
      } catch (err) {
        setError('Не удалось удалить роадмап. Попробуйте еще раз.');
        console.error(err);
      }
    }
  };

  const updateStepInTree = (steps, stepId) => {
    return steps.map(step => {
      if (step.id === stepId) { return { ...step, is_done: !step.is_done }; }
      if (step.children && step.children.length > 0) { return { ...step, children: updateStepInTree(step.children, stepId) }; }
      return step;
    });
  };

  const addChildrenToStep = (steps, parentId, newChildren) => {
    return steps.map(step => {
      if (step.id === parentId) { return { ...step, children: newChildren }; }
      if (step.children && step.children.length > 0) { return { ...step, children: addChildrenToStep(step.children, parentId, newChildren) }; }
      return step;
    });
  };

  const handleToggleStep = async (stepId) => {
    const updatedSteps = updateStepInTree(currentRoadmap.steps, stepId);
    setCurrentRoadmap({ ...currentRoadmap, steps: updatedSteps });
    try {
      await axios.put(`/api/steps/${stepId}/toggle`);
    } catch (error) {
      console.error("Ошибка при обновлении шага:", error);
      const revertedSteps = updateStepInTree(currentRoadmap.steps, stepId); 
      setCurrentRoadmap({ ...currentRoadmap, steps: revertedSteps });
      setError("Не удалось сохранить изменение.");
    }
  };

  const handleDecomposeStep = async (stepId) => {
    try {
      const response = await axios.post(`/api/steps/${stepId}/decompose`);
      const newChildren = response.data;
      const updatedSteps = addChildrenToStep(currentRoadmap.steps, stepId, newChildren);
      setCurrentRoadmap({ ...currentRoadmap, steps: updatedSteps });
    } catch (error) {
      console.error("Ошибка при декомпозиции:", error);
      setError("Ошибка на стороне GigaChat. Не удалось создать подзадачи. Пожалуйста, попробуйте еще раз.");
    }
  };

  const renderContent = () => {
    if (view === 'loading' || isLoading) {
      return <div className="centered-spinner"><Spinner size="large" /></div>;
    }
    if (view === 'list') {
      return <ListScreen 
                roadmaps={roadmapList} 
                isLoading={isLoading} 
                onSelectRoadmap={handleSelectRoadmap} 
                onCreateNew={() => setView('create')}
             />;
    }
    if (view === 'roadmap' && currentRoadmap) {
      return <RoadmapScreen 
                roadmap={currentRoadmap} 
                onBack={handleBack} 
                onToggle={handleToggleStep} 
                onDecompose={handleDecomposeStep}
                onDelete={handleDeleteRoadmap}
             />;
    }
    return <CreateScreen 
              maxUserId={maxUserId} 
              onRoadmapCreated={handleRoadmapCreated} 
              onShowList={() => setView('list')} 
           />;
  };

  return (
    <div className="app-container">
      {error && !isLoading && <p className="error-message">{error}</p>}
      {renderContent()}
    </div>
  );
}

export default App;