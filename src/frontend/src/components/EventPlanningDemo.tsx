import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { Progress } from './ui/progress'
import { ScrollArea } from './ui/scroll-area'
import { Separator } from './ui/separator'
import { 
  Bot, 
  Calendar, 
  DollarSign, 
  MapPin, 
  Users, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Wrench,
} from 'lucide-react'
import { toast } from 'sonner'
import { AgentConversation } from './AgentConversation'
import { McpToolSelector } from './McpToolSelector'

interface Agent {
  id: string
  name: string
  role: string
  status: 'idle' | 'working' | 'completed' | 'error'
  avatar: React.ReactNode
  lastMessage?: string
}

interface EventRequest {
  eventType: string
  attendees: number
  budget: number
  date: string
  location: string
  requirements: string
}

interface AgentCollaborationState {
  isActive: boolean
  currentRound: number
  totalRounds: number
  activeAgents: string[]
}

export function EventPlanningDemo() {
  const [eventRequest, setEventRequest] = useState<EventRequest>({
    eventType: '',
    attendees: 50,
    budget: 10000,
    date: '',
    location: '',
    requirements: ''
  })
  
  const [isPlanning, setIsPlanning] = useState(false)
  const [planningProgress, setPlanningProgress] = useState(0)
  const [activeTab, setActiveTab] = useState('setup')
  const [selectedMcpTools, setSelectedMcpTools] = useState<string[]>(['venue_search', 'weather_api', 'budget_calculator'])
  const [collaborationState, setCollaborationState] = useState<AgentCollaborationState>({
    isActive: false,
    currentRound: 0,
    totalRounds: 3,
    activeAgents: []
  })
  
  const [agents] = useState<Agent[]>([
    {
      id: 'coordinator',
      name: 'Event Coordinator',
      role: 'Orchestrates the overall planning process',
      status: 'idle',
      avatar: <Bot className="h-6 w-6 text-blue-500" />
    },
    {
      id: 'venue',
      name: 'Venue Specialist',
      role: 'Researches and recommends venues',
      status: 'idle',
      avatar: <MapPin className="h-6 w-6 text-green-500" />
    },
    {
      id: 'budget',
      name: 'Budget Analyst',
      role: 'Manages costs and financial constraints',
      status: 'idle',
      avatar: <DollarSign className="h-6 w-6 text-yellow-500" />
    },
    {
      id: 'catering',
      name: 'Catering Coordinator',
      role: 'Handles food and beverage planning',
      status: 'idle',
      avatar: <Users className="h-6 w-6 text-purple-500" />
    },
    {
      id: 'logistics',
      name: 'Logistics Manager',
      role: 'Coordinates schedules and resources',
      status: 'idle',
      avatar: <Clock className="h-6 w-6 text-red-500" />
    }
  ])

  const handleStartPlanning = async () => {
    if (!eventRequest.eventType || !eventRequest.date) {
      toast.error('Please fill in the event type and date')
      return
    }

    setIsPlanning(true)
    setPlanningProgress(0)
    setActiveTab('agents')
    setCollaborationState({
      isActive: true,
      currentRound: 1,
      totalRounds: 3,
      activeAgents: ['event_planner', 'venue_researcher', 'budget_analyst']
    })
    
    try {
      const response = await fetch('/api/v1/learning/multi_agent/simple_collaboration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task: `Plan a ${eventRequest.eventType} for ${eventRequest.attendees} people with $${eventRequest.budget} budget on ${eventRequest.date} in ${eventRequest.location}. Requirements: ${eventRequest.requirements}`,
          primary_agent: 'event_planner',
          secondary_agent: 'budget_analyst'
        })
      })
      
      if (!response.ok) {
        throw new Error('Backend not available - using demo mode')
      }
      
      await response.json()
      toast.success('Event planning completed successfully!')
      
    } catch (error) {
      toast.info('Running in demo mode - backend not available')
      simulatePlanning()
    }
  }

  const simulatePlanning = () => {
    const steps = [
      { progress: 20, message: 'Event Coordinator analyzing requirements...' },
      { progress: 40, message: 'Venue Specialist searching locations...' },
      { progress: 60, message: 'Budget Analyst calculating costs...' },
      { progress: 80, message: 'Catering Coordinator planning menu...' },
      { progress: 100, message: 'Logistics Manager finalizing schedule...' }
    ]
    
    steps.forEach((step, index) => {
      setTimeout(() => {
        setPlanningProgress(step.progress)
        if (step.progress === 100) {
          setIsPlanning(false)
          setActiveTab('results')
          setCollaborationState(prev => ({ ...prev, isActive: false }))
          toast.success('Event planning completed!')
        }
      }, (index + 1) * 1500)
    })
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2 mb-6">
        <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
          Experience AI agent collaboration in action. Watch specialized agents work together 
          to plan your perfect event using the Microsoft Agent Framework.
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="setup">Event Setup</TabsTrigger>
          <TabsTrigger value="agents">Agent Collaboration</TabsTrigger>
          <TabsTrigger value="workflow">Workflow Monitor</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>

        <TabsContent value="setup" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Event Requirements</CardTitle>
              <CardDescription>
                Define your event specifications for the AI agents to process
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium">Event Type</label>
                  <Input
                    placeholder="e.g., Corporate Conference, Wedding, Birthday Party"
                    value={eventRequest.eventType}
                    onChange={(e) => setEventRequest(prev => ({ ...prev, eventType: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Expected Attendees</label>
                  <Input
                    type="number"
                    value={eventRequest.attendees}
                    onChange={(e) => setEventRequest(prev => ({ ...prev, attendees: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Budget ($)</label>
                  <Input
                    type="number"
                    value={eventRequest.budget}
                    onChange={(e) => setEventRequest(prev => ({ ...prev, budget: parseInt(e.target.value) || 0 }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Event Date</label>
                  <Input
                    type="date"
                    value={eventRequest.date}
                    onChange={(e) => setEventRequest(prev => ({ ...prev, date: e.target.value }))}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Preferred Location</label>
                  <Input
                    placeholder="e.g., Seattle, WA or Downtown area"
                    value={eventRequest.location}
                    onChange={(e) => setEventRequest(prev => ({ ...prev, location: e.target.value }))}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Special Requirements</label>
                <Textarea
                  placeholder="Any specific requirements, preferences, or constraints..."
                  value={eventRequest.requirements}
                  onChange={(e) => setEventRequest(prev => ({ ...prev, requirements: e.target.value }))}
                  rows={3}
                />
              </div>
              
              <Separator />
              
              <McpToolSelector 
                selectedTools={selectedMcpTools}
                onToolChange={setSelectedMcpTools}
              />
              
              <Button 
                onClick={handleStartPlanning} 
                disabled={isPlanning}
                className="w-full"
                size="lg"
              >
                {isPlanning ? (
                  <>
                    <Pause className="mr-2 h-4 w-4" />
                    Planning in Progress...
                  </>
                ) : (
                  <>
                    <Play className="mr-2 h-4 w-4" />
                    Start Agent Collaboration
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="agents" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Bot className="h-5 w-5" />
                  <span>Agent Status</span>
                </CardTitle>
                <CardDescription>
                  Monitor specialized agents working on your event
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {isPlanning && (
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>Planning Progress</span>
                        <span>{planningProgress}%</span>
                      </div>
                      <Progress value={planningProgress} className="w-full" />
                    </div>
                  )}
                  
                  <div className="grid gap-3">
                    {agents.map((agent) => (
                      <Card key={agent.id} className="p-3">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            {agent.avatar}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between">
                              <h3 className="font-medium text-sm">{agent.name}</h3>
                              <Badge variant={agent.status === 'working' ? 'default' : 'secondary'} className="text-xs">
                                {agent.status}
                              </Badge>
                            </div>
                            <p className="text-xs text-muted-foreground">{agent.role}</p>
                            {selectedMcpTools.length > 0 && (
                              <div className="flex items-center space-x-1 mt-1">
                                <Wrench className="h-3 w-3 text-muted-foreground" />
                                <span className="text-xs text-muted-foreground">
                                  {selectedMcpTools.length} MCP tools available
                                </span>
                              </div>
                            )}
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <AgentConversation 
              isActive={collaborationState.isActive}
              eventRequest={eventRequest}
            />
          </div>
        </TabsContent>

        <TabsContent value="workflow" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Workflow Orchestration</CardTitle>
              <CardDescription>
                Real-time view of agent coordination and decision-making
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96 w-full border rounded-md p-4">
                <div className="space-y-4">
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">Event Coordinator initialized</p>
                      <p className="text-xs text-muted-foreground">Analyzing event requirements and creating task distribution plan</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="flex items-start space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">Venue Specialist activated</p>
                      <p className="text-xs text-muted-foreground">Searching for venues matching capacity and location requirements</p>
                    </div>
                  </div>
                  <Separator />
                  <div className="flex items-start space-x-3">
                    <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium">Budget Analyst reviewing constraints</p>
                      <p className="text-xs text-muted-foreground">Calculating cost breakdown and identifying optimization opportunities</p>
                    </div>
                  </div>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="results" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Event Plan Results</CardTitle>
              <CardDescription>
                Comprehensive event plan generated by AI agent collaboration
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="p-4">
                    <div className="flex items-center space-x-2">
                      <MapPin className="h-5 w-5 text-green-500" />
                      <h3 className="font-medium">Venue</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      Seattle Convention Center<br />
                      Main Hall - Capacity: 200<br />
                      $2,500/day
                    </p>
                  </Card>
                  <Card className="p-4">
                    <div className="flex items-center space-x-2">
                      <DollarSign className="h-5 w-5 text-yellow-500" />
                      <h3 className="font-medium">Budget</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      Total: $9,750<br />
                      Under budget by $250<br />
                      Contingency: 5%
                    </p>
                  </Card>
                  <Card className="p-4">
                    <div className="flex items-center space-x-2">
                      <Calendar className="h-5 w-5 text-blue-500" />
                      <h3 className="font-medium">Timeline</h3>
                    </div>
                    <p className="text-sm text-muted-foreground mt-2">
                      Setup: 8:00 AM<br />
                      Event: 10:00 AM - 4:00 PM<br />
                      Cleanup: 4:00 PM - 6:00 PM
                    </p>
                  </Card>
                </div>
                
                <Button className="w-full" variant="outline">
                  <RotateCcw className="mr-2 h-4 w-4" />
                  Plan Another Event
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
