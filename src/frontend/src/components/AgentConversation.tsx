import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Badge } from './ui/badge'
import { ScrollArea } from './ui/scroll-area'
import { Separator } from './ui/separator'
import { Bot, MessageCircle, Users, Clock } from 'lucide-react'

interface AgentMessage {
  agent_name: string
  agent_type: string
  message: string
  timestamp: string
  round_number: number
  message_type: 'proposal' | 'feedback' | 'question' | 'conclusion'
}

interface AgentConversationProps {
  isActive: boolean
  eventRequest: any
}

const agentIcons: Record<string, React.ReactNode> = {
  'event_planner': <Bot className="h-4 w-4 text-blue-500" />,
  'venue_researcher': <Bot className="h-4 w-4 text-green-500" />,
  'budget_analyst': <Bot className="h-4 w-4 text-yellow-500" />,
  'catering_coordinator': <Bot className="h-4 w-4 text-purple-500" />,
  'logistics_manager': <Bot className="h-4 w-4 text-red-500" />
}

export function AgentConversation({ isActive, eventRequest }: AgentConversationProps) {
  const [messages, setMessages] = useState<AgentMessage[]>([])
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'simulation'>('disconnected')

  useEffect(() => {
    if (isActive && eventRequest.eventType) {
      attemptWebSocketConnection()
    }
    
    return () => {
      if (wsConnection) {
        wsConnection.close()
      }
    }
  }, [isActive, eventRequest])

  const attemptWebSocketConnection = () => {
    try {
      setConnectionStatus('connecting')
      const ws = new WebSocket(`ws://localhost:8000/ws/workflow/demo-${Date.now()}`)
      
      ws.onopen = () => {
        setConnectionStatus('connected')
        setWsConnection(ws)
      }
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'agent_response') {
            setMessages(prev => [...prev, data.data])
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error)
        }
      }
      
      ws.onerror = () => {
        setConnectionStatus('simulation')
        simulateAgentConversation()
      }
      
      ws.onclose = () => {
        setConnectionStatus('disconnected')
      }
      
      setTimeout(() => {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.close()
          setConnectionStatus('simulation')
          simulateAgentConversation()
        }
      }, 3000)
      
    } catch (error) {
      setConnectionStatus('simulation')
      simulateAgentConversation()
    }
  }

  const simulateAgentConversation = () => {
    const simulatedMessages: AgentMessage[] = [
      {
        agent_name: 'EventPlannerAgent',
        agent_type: 'event_planner',
        message: `I'll coordinate planning for your ${eventRequest.eventType}. Let me analyze the requirements: ${eventRequest.attendees} attendees, $${eventRequest.budget} budget, location: ${eventRequest.location}. I'll delegate specific tasks to our specialist agents.`,
        timestamp: new Date().toISOString(),
        round_number: 1,
        message_type: 'proposal'
      },
      {
        agent_name: 'VenueResearcherAgent',
        agent_type: 'venue_researcher',
        message: `I'll search for venues in ${eventRequest.location} that can accommodate ${eventRequest.attendees} people. Using MCP venue search tools to find options within your budget range. I'll prioritize venues with good accessibility and parking.`,
        timestamp: new Date(Date.now() + 2000).toISOString(),
        round_number: 1,
        message_type: 'feedback'
      },
      {
        agent_name: 'BudgetAnalystAgent',
        agent_type: 'budget_analyst',
        message: `Based on the $${eventRequest.budget} budget, I recommend allocating 30% for venue ($${Math.round(eventRequest.budget * 0.3)}), 40% for catering ($${Math.round(eventRequest.budget * 0.4)}), and 30% for other expenses. I'll use financial analysis tools to optimize cost distribution.`,
        timestamp: new Date(Date.now() + 4000).toISOString(),
        round_number: 1,
        message_type: 'feedback'
      },
      {
        agent_name: 'CateringCoordinatorAgent',
        agent_type: 'catering_coordinator',
        message: `For ${eventRequest.attendees} guests, I'll plan appropriate catering options. Using MCP tools to check dietary restrictions and local vendor availability. I'll coordinate with the budget analyst to ensure we stay within the allocated catering budget.`,
        timestamp: new Date(Date.now() + 6000).toISOString(),
        round_number: 2,
        message_type: 'proposal'
      },
      {
        agent_name: 'EventPlannerAgent',
        agent_type: 'event_planner',
        message: `Excellent collaboration! I'm synthesizing all recommendations. The venue options from our researcher, budget allocation from our analyst, and catering plans are well-coordinated. This demonstrates effective A2A communication and MCP tool integration.`,
        timestamp: new Date(Date.now() + 8000).toISOString(),
        round_number: 2,
        message_type: 'conclusion'
      }
    ]

    simulatedMessages.forEach((message, index) => {
      setTimeout(() => {
        setMessages(prev => [...prev, message])
      }, index * 2000)
    })
  }

  const getMessageTypeColor = (type: string) => {
    switch (type) {
      case 'proposal': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'feedback': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'question': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'conclusion': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <MessageCircle className="h-5 w-5" />
            <span>Agent-to-Agent Communication</span>
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Badge variant={connectionStatus === 'connected' ? 'default' : 'secondary'}>
              {connectionStatus === 'connected' ? 'Live WebSocket' : 
               connectionStatus === 'simulation' ? 'Demo Mode' : 
               connectionStatus === 'connecting' ? 'Connecting...' : 'Offline'}
            </Badge>
            {messages.length > 0 && (
              <Badge variant="outline" className="flex items-center space-x-1">
                <Users className="h-3 w-3" />
                <span>{new Set(messages.map(m => m.agent_type)).size} agents</span>
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-96">
          {messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center space-y-2">
                <MessageCircle className="h-12 w-12 mx-auto opacity-50" />
                <p>Agent conversation will appear here</p>
                <p className="text-xs">Start event planning to see A2A communication</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-1">
                      {agentIcons[message.agent_type] || <Bot className="h-4 w-4" />}
                    </div>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium text-sm">{message.agent_name}</span>
                        <Badge variant="outline" className={`text-xs ${getMessageTypeColor(message.message_type)}`}>
                          {message.message_type}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          Round {message.round_number}
                        </Badge>
                        <div className="flex items-center space-x-1 text-xs text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground leading-relaxed">
                        {message.message}
                      </p>
                    </div>
                  </div>
                  {index < messages.length - 1 && <Separator className="my-3" />}
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
