import React, { useEffect, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  BarChart3,
  Bell,
  Bot,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  FolderKanban,
  LayoutDashboard,
  Plus,
  RefreshCw,
  Search,
  Settings,
  Users,
} from 'lucide-react'

const API_BASE_URL = '/api'

const cn = (...classes) => classes.filter(Boolean).join(' ')

const Card = ({ children, className }) => (
  <div className={cn('bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden', className)}>
    {children}
  </div>
)

const Button = ({ children, variant = 'primary', size = 'default', className, onClick, disabled, type = 'button' }) => {
  const baseStyle =
    'inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed'

  const variants = {
    primary: 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20',
    secondary: 'bg-zinc-800 hover:bg-zinc-700 text-zinc-100 border border-zinc-700',
    outline: 'bg-transparent hover:bg-zinc-800 text-zinc-300 border border-zinc-700',
    ghost: 'bg-transparent hover:bg-zinc-800/50 text-zinc-400 hover:text-white',
    danger: 'bg-red-900/20 hover:bg-red-900/40 text-red-400 border border-red-900/50',
  }

  const sizes = {
    default: 'px-4 py-2 text-sm',
    sm: 'px-3 py-1.5 text-xs',
    icon: 'p-2',
  }

  return (
    <button onClick={onClick} disabled={disabled} type={type} className={cn(baseStyle, variants[variant], sizes[size], className)}>
      {children}
    </button>
  )
}

const Badge = ({ children, variant = 'default' }) => {
  const variants = {
    default: 'bg-zinc-800 text-zinc-300 border-zinc-700',
    success: 'bg-emerald-950/50 text-emerald-400 border-emerald-900',
    warning: 'bg-amber-950/50 text-amber-400 border-amber-900',
    error: 'bg-red-950/50 text-red-400 border-red-900',
    info: 'bg-blue-950/50 text-blue-400 border-blue-900',
  }
  return (
    <span className={cn('px-2.5 py-0.5 rounded-full text-xs font-medium border', variants[variant])}>{children}</span>
  )
}

const Input = ({ label, ...props }) => (
  <div className="space-y-1.5">
    {label && <label className="text-xs font-medium text-zinc-400">{label}</label>}
    <input
      className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all placeholder:text-zinc-600"
      {...props}
    />
  </div>
)

const StatCard = ({ title, value, change, icon: Icon, trend }) => (
  <Card className="p-6">
    <div className="flex items-center justify-between mb-4">
      <h3 className="text-zinc-400 text-sm font-medium">{title}</h3>
      <div className="p-2 bg-zinc-800/50 rounded-lg text-zinc-400">
        <Icon size={18} />
      </div>
    </div>
    <div className="flex items-end justify-between">
      <div>
        <p className="text-2xl font-bold text-white">{value}</p>
        <div className="flex items-center gap-1 mt-1">
          {trend === 'up' && (
            <div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-b-[6px] border-b-emerald-500"></div>
          )}
          {trend === 'down' && (
            <div className="w-0 h-0 border-l-[4px] border-l-transparent border-r-[4px] border-r-transparent border-t-[6px] border-t-red-500"></div>
          )}
          <p
            className={cn(
              'text-xs font-medium',
              trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-zinc-500'
            )}
          >
            {change}
          </p>
        </div>
      </div>
    </div>
  </Card>
)

const RedFlagsPanel = ({ data }) => {
  if (!data) {
    return (
      <Card className="p-6 border-zinc-800 flex items-center justify-center text-zinc-500 text-sm h-full min-h-[200px]">
        <RefreshCw className="animate-spin mr-2" size={16} /> Загрузка статуса системы...
      </Card>
    )
  }

  const hasCritical = data.failed_runs?.alert || data.missing_metrics?.alert

  return (
    <Card className={cn('p-0 h-full', hasCritical ? 'border-red-900/30 bg-red-950/5' : '')}>
      <div className={cn('p-4 border-b flex items-center justify-between', hasCritical ? 'border-red-900/20' : 'border-zinc-800')}>
        <div className="flex items-center gap-2">
          <AlertTriangle className={hasCritical ? 'text-red-500' : 'text-zinc-400'} size={18} />
          <h3 className={cn('font-medium', hasCritical ? 'text-red-500' : 'text-zinc-200')}>Системные Алерты</h3>
        </div>
        {hasCritical ? <Badge variant="error">Critical</Badge> : <Badge variant="success">Healthy</Badge>}
      </div>
      <div className="p-4 space-y-3">
        {data.failed_runs?.alert ? (
          <div className="flex items-start gap-3 p-3 bg-red-500/10 rounded-lg border border-red-500/20">
            <div className="w-1.5 h-1.5 rounded-full bg-red-500 mt-2" />
            <div>
              <p className="text-sm text-red-200 font-medium">Высокий процент сбоев</p>
              <p className="text-xs text-red-400/80 mt-0.5">{data.failed_runs.last_24h.percentage}% запусков упали за 24ч</p>
            </div>
          </div>
        ) : !hasCritical ? (
          <div className="flex flex-col items-center justify-center py-8 text-zinc-500 space-y-2">
            <CheckCircle2 size={32} className="text-emerald-500/20" />
            <p className="text-sm">Система работает стабильно</p>
          </div>
        ) : null}
      </div>
    </Card>
  )
}

const DashboardHome = () => {
  const [redFlags, setRedFlags] = useState(null)
  const [stats, setStats] = useState({ personas: '-', published: '-', projects: '-' })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const rfRes = await fetch(`${API_BASE_URL}/red-flags`)
        if (rfRes.ok) setRedFlags(await rfRes.json())

        const [pRes, prRes] = await Promise.all([
          fetch(`${API_BASE_URL}/personas`),
          fetch(`${API_BASE_URL}/projects`),
        ])

        const personas = pRes.ok ? await pRes.json() : []
        const projects = prRes.ok ? await prRes.json() : []

        setStats({
          personas: personas.length,
          projects: projects.length,
          published: '-',
        })
      } catch (err) {
        console.error('Dashboard data load error:', err)
      }
    }
    fetchData()
  }, [])

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Обзор</h1>
          <p className="text-zinc-400">Центр управления цифровыми личностями.</p>
        </div>
        <div className="text-xs text-zinc-600 font-mono">v1.0.0</div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Всего Персон" value={stats.personas} change="Активны" icon={Users} trend="neutral" />
        <StatCard title="Опубликовано" value={stats.published} change="За все время" icon={LayoutDashboard} trend="neutral" />
        <StatCard title="Проекты" value={stats.projects} change="В работе" icon={FolderKanban} trend="neutral" />
        <StatCard title="Здоровье API" value="100%" change="Stable" icon={Activity} trend="up" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card className="p-0">
            <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
              <h3 className="text-lg font-medium text-white">Последняя Активность</h3>
              <Button variant="ghost" size="sm">
                Все логи
              </Button>
            </div>
            <div className="p-6">
              <div className="text-center py-8 text-zinc-500 text-sm border-2 border-dashed border-zinc-800/50 rounded-lg">
                Нет недавней активности для отображения.
              </div>
            </div>
          </Card>
        </div>
        <div className="space-y-6">
          <RedFlagsPanel data={redFlags} />
        </div>
      </div>
    </div>
  )
}

const CreatePersonaModal = ({ onClose }) => {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({ persona_name: '', inspiration_source: '', language: 'ru', notes: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/genesis/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      })
      if (!response.ok) throw new Error('Failed')
      const data = await response.json()
      alert(`Задача Genesis запущена! ID: ${data.job_id}`)
      onClose()
    } catch (err) {
      alert('Ошибка при запуске Genesis. Проверьте консоль.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
      <Card className="w-full max-w-lg bg-zinc-950 border-zinc-800 shadow-2xl">
        <div className="p-6 border-b border-zinc-800 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-white">Создать Новую Персону</h2>
            <p className="text-sm text-zinc-400 mt-1">Запуск Genesis Engine для генерации личности.</p>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <Input
            label="Имя Персоны"
            placeholder="например, Алексей"
            required
            value={formData.persona_name}
            onChange={(e) => setFormData({ ...formData, persona_name: e.target.value })}
          />
          <Input
            label="Источник Вдохновения"
            placeholder="например, Тим Келлер, Достоевский"
            value={formData.inspiration_source}
            onChange={(e) => setFormData({ ...formData, inspiration_source: e.target.value })}
          />
          <div>
            <label className="text-xs font-medium text-zinc-400 mb-1.5 block">Язык</label>
            <select
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all"
              value={formData.language}
              onChange={(e) => setFormData({ ...formData, language: e.target.value })}
            >
              <option value="en">English</option>
              <option value="ru">Русский</option>
            </select>
          </div>
          <div>
            <label className="text-xs font-medium text-zinc-400 mb-1.5 block">Заметки / Контекст</label>
            <textarea
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100 h-24 resize-none focus:outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 transition-all placeholder:text-zinc-600"
              placeholder="Опишите ключевые ценности, миссию и т.д..."
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
            />
          </div>
          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? (
                <span className="flex items-center gap-2">
                  <RefreshCw className="animate-spin" size={14} /> Запуск...
                </span>
              ) : (
                'Запустить Genesis'
              )}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

const CreateProjectModal = ({ onClose }) => {
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({ name: '', persona_id: '', channels: 'telegram' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/projects`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...formData, channels: [formData.channels] }),
      })
      if (!response.ok) throw new Error('Failed')
      const data = await response.json()
      alert(`Проект создан! ID: ${data.id}`)
      onClose()
    } catch (err) {
      alert('Ошибка при создании проекта. Убедитесь, что ID персоны верный.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in duration-200">
      <Card className="w-full max-w-lg bg-zinc-950 border-zinc-800 shadow-2xl">
        <div className="p-6 border-b border-zinc-800">
          <h2 className="text-xl font-bold text-white">Создать Новый Проект</h2>
          <p className="text-sm text-zinc-400 mt-1">Организация контент-планов для персоны.</p>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <Input
            label="Название Проекта"
            required
            placeholder="Мой блог в Telegram"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          />
          <Input
            label="ID Персоны (UUID)"
            required
            placeholder="Скопируйте UUID из вкладки 'Персоны'"
            value={formData.persona_id}
            onChange={(e) => setFormData({ ...formData, persona_id: e.target.value })}
          />
          <div>
            <label className="text-xs font-medium text-zinc-400 mb-1.5 block">Канал</label>
            <select
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-100"
              value={formData.channels}
              onChange={(e) => setFormData({ ...formData, channels: e.target.value })}
            >
              <option value="telegram">Telegram</option>
              <option value="instagram">Instagram</option>
            </select>
          </div>
          <div className="flex gap-3 pt-4">
            <Button variant="outline" className="flex-1" onClick={onClose}>
              Отмена
            </Button>
            <Button type="submit" className="flex-1" disabled={loading}>
              {loading ? 'Создание...' : 'Создать Проект'}
            </Button>
          </div>
        </form>
      </Card>
    </div>
  )
}

const PersonasView = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [personas, setPersonas] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchPersonas = () => {
    setLoading(true)
    fetch(`${API_BASE_URL}/personas`)
      .then((res) => {
        if (!res.ok) throw new Error('API Error')
        return res.json()
      })
      .then((data) => {
        setPersonas(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error('Failed to fetch personas', err)
        setLoading(false)
        if (personas.length === 0) setPersonas([])
      })
  }

  useEffect(() => {
    fetchPersonas()
  }, [])

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Персоны</h1>
          <p className="text-zinc-400">Управление вашими ИИ-сущностями.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={16} />
          Создать Персону
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64 text-zinc-500 gap-2">
          <RefreshCw className="animate-spin" size={20} /> Загрузка данных...
        </div>
      ) : personas.length === 0 ? (
        <Card className="p-12 border-dashed flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-zinc-800/50 rounded-full flex items-center justify-center mb-4 text-zinc-500">
            <Bot size={32} />
          </div>
          <h3 className="text-lg font-medium text-white mb-2">Нет персон</h3>
          <p className="text-zinc-500 mb-6 max-w-sm">Создайте свою первую цифровую личность, чтобы начать генерировать контент.</p>
          <Button onClick={() => setIsModalOpen(true)}>Создать Персону</Button>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {personas.map((persona) => (
            <Card key={persona.id} className="p-6 hover:border-zinc-600 transition-colors cursor-pointer group flex flex-col">
              <div className="flex items-start justify-between mb-4">
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600/20 to-purple-600/20 flex items-center justify-center text-blue-400 group-hover:text-white group-hover:from-blue-600 group-hover:to-purple-600 transition-all">
                  <Bot size={24} />
                </div>
                <Badge variant="success">Active</Badge>
              </div>
              <div className="mb-4 flex-1">
                <h3 className="text-lg font-bold text-white mb-1 line-clamp-1">{persona.name}</h3>
                <p className="text-sm text-zinc-500 font-mono text-xs">{persona.id.substring(0, 8)}...</p>
              </div>

              <div className="space-y-3 pt-4 border-t border-zinc-800">
                <div className="flex justify-between text-xs text-zinc-400">
                  <span>Версия</span>
                  <span className="text-zinc-200">{persona.active_version}</span>
                </div>
                <div className="flex justify-between text-xs text-zinc-400">
                  <span>Создана</span>
                  <span className="text-zinc-200">{new Date(persona.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="mt-6 flex gap-2">
                <Button variant="outline" size="sm" className="w-full">
                  Детали
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {isModalOpen && <CreatePersonaModal onClose={() => { setIsModalOpen(false); fetchPersonas() }} />}
    </div>
  )
}

const ProjectsView = () => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchProjects = () => {
    setLoading(true)
    fetch(`${API_BASE_URL}/projects`)
      .then((res) => res.json())
      .then((data) => {
        setProjects(data)
        setLoading(false)
      })
      .catch((err) => {
        console.error(err)
        setLoading(false)
      })
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Проекты</h1>
          <p className="text-zinc-400">Контент-планы и публикации.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus size={16} />
          Новый Проект
        </Button>
      </div>

      <Card className="overflow-hidden">
        <div className="w-full overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="bg-zinc-900/50 text-zinc-400 border-b border-zinc-800">
              <tr>
                <th className="px-6 py-4 font-medium">Название</th>
                <th className="px-6 py-4 font-medium">Персона</th>
                <th className="px-6 py-4 font-medium">Каналы</th>
                <th className="px-6 py-4 font-medium">Создан</th>
                <th className="px-6 py-4 font-medium text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800">
              {loading ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-zinc-500">
                    Загрузка...
                  </td>
                </tr>
              ) : projects.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-zinc-500">
                    Нет активных проектов
                  </td>
                </tr>
              ) : (
                projects.map((p) => (
                  <tr key={p.id} className="hover:bg-zinc-800/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">{p.name}</td>
                    <td className="px-6 py-4 text-zinc-400 font-mono text-xs">{p.persona_id.substring(0, 8)}...</td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        {p.channels.map((c) => (
                          <Badge key={c} variant="info">
                            {c}
                          </Badge>
                        ))}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-zinc-400">{new Date(p.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                      <Button variant="ghost" className="h-8 w-8 p-0">
                        <ChevronRight size={16} />
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {isModalOpen && <CreateProjectModal onClose={() => { setIsModalOpen(false); fetchProjects() }} />}
    </div>
  )
}

const SidebarItem = ({ icon: Icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={cn(
      'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all group',
      active ? 'bg-blue-600/10 text-blue-400' : 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100'
    )}
  >
    <Icon size={18} className={cn('transition-colors', active ? 'text-blue-400' : 'text-zinc-500 group-hover:text-zinc-300')} />
    {label}
  </button>
)

const App = () => {
  const [activeView, setActiveView] = useState('dashboard')

  return (
    <div className="min-h-screen bg-black text-zinc-100 font-sans selection:bg-blue-500/30">
      <div className="flex h-screen overflow-hidden">
        <aside className="w-64 border-r border-zinc-800 bg-zinc-950 flex flex-col">
          <div className="p-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center text-white font-bold shadow-lg shadow-blue-900/20">
                M
              </div>
              <span className="font-bold text-lg tracking-tight">MPIS</span>
            </div>
          </div>

          <nav className="flex-1 px-4 space-y-1">
            <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-3 mb-2 mt-4">Платформа</div>
            <SidebarItem icon={LayoutDashboard} label="Обзор" active={activeView === 'dashboard'} onClick={() => setActiveView('dashboard')} />
            <SidebarItem icon={Users} label="Персоны" active={activeView === 'personas'} onClick={() => setActiveView('personas')} />
            <SidebarItem icon={FolderKanban} label="Проекты" active={activeView === 'projects'} onClick={() => setActiveView('projects')} />
            <SidebarItem icon={BarChart3} label="Аналитика" active={activeView === 'analytics'} onClick={() => setActiveView('analytics')} />

            <div className="text-xs font-semibold text-zinc-500 uppercase tracking-wider px-3 mb-2 mt-8">Система</div>
            <SidebarItem icon={Settings} label="Настройки" active={activeView === 'settings'} onClick={() => setActiveView('settings')} />
          </nav>

          <div className="p-4 border-t border-zinc-800">
            <div className="flex items-center gap-3 px-3 py-2 bg-zinc-900/50 rounded-xl border border-zinc-800/50">
              <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400">A</div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">Admin</p>
                <p className="text-xs text-zinc-500 truncate">Online</p>
              </div>
            </div>
          </div>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden bg-black relative">
          <header className="h-16 border-b border-zinc-800 bg-black/50 backdrop-blur-xl flex items-center justify-between px-8 sticky top-0 z-10">
            <div className="flex items-center gap-4 text-sm text-zinc-400">
              <span className="flex items-center gap-2 px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]"></div>
                v1.0.0
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-white">
                <Search size={18} />
              </Button>
              <Button variant="ghost" size="icon" className="text-zinc-400 hover:text-white relative">
                <Bell size={18} />
                <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-red-500 rounded-full border border-black"></span>
              </Button>
            </div>
          </header>

          <div className="flex-1 overflow-auto p-8">
            <div className="max-w-7xl mx-auto">
              {activeView === 'dashboard' && <DashboardHome />}
              {activeView === 'personas' && <PersonasView />}
              {activeView === 'projects' && <ProjectsView />}
              {activeView === 'analytics' && (
                <div className="flex flex-col items-center justify-center h-96 text-zinc-500">
                  <BarChart3 size={48} className="mb-4 opacity-20" />
                  <p>Модуль аналитики в разработке</p>
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App
