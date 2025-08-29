
import { Link, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { ModeToggle } from './ui/mode-toggle'
import { Bot, BookOpen, Zap } from 'lucide-react'

export function Navigation() {
  const location = useLocation()

  const navItems = [
    {
      path: '/',
      label: 'Event Planning Demo',
      icon: Bot,
      description: 'AI Agent Orchestration'
    },
    {
      path: '/learning',
      label: 'Learning Progression',
      icon: BookOpen,
      description: '6-Level Framework'
    },
    {
      path: '/specs-to-agents',
      label: 'Specs-to-Agents',
      icon: Zap,
      description: 'Agent Creator'
    }
  ]

  return (
    <nav className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4">
        <div className="flex h-16 items-center justify-between">
          <div className="flex items-center space-x-8">
            <Link to="/" className="flex items-center space-x-2">
              <Bot className="h-6 w-6 text-primary" />
              <span className="font-bold text-xl">Microsoft Agent Framework</span>
            </Link>
            
            <div className="hidden md:flex items-center space-x-6">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-primary text-primary-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <div className="flex flex-col">
                      <span>{item.label}</span>
                      <span className="text-xs opacity-70">{item.description}</span>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <ModeToggle />
            <Button variant="outline" size="sm" asChild>
              <a href="https://github.com/microsoft/agent-framework" target="_blank" rel="noopener noreferrer">
                GitHub
              </a>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}
