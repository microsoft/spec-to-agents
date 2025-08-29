import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'
import { Progress } from './ui/progress'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { 
  Bot, 
  Wrench, 
  Users, 
  Workflow, 
  Zap, 
  HandHeart,
  ChevronRight,
  CheckCircle,
  Lock
} from 'lucide-react'

interface LearningLevel {
  id: number
  title: string
  description: string
  icon: React.ReactNode
  status: 'completed' | 'current' | 'locked'
  concepts: string[]
  examples: string[]
}

export function LearningProgression() {
  const [selectedLevel, setSelectedLevel] = useState(1)
  
  const learningLevels: LearningLevel[] = [
    {
      id: 1,
      title: 'Basic Agents',
      description: 'Single agent conversations and instructions',
      icon: <Bot className="h-6 w-6" />,
      status: 'completed',
      concepts: [
        'Agent creation and configuration',
        'Instruction-based behavior',
        'Basic prompt engineering',
        'Single agent interactions'
      ],
      examples: [
        'Simple chat with event planning agent',
        'Custom instruction configuration',
        'Agent personality customization'
      ]
    },
    {
      id: 2,
      title: 'Agent Tools',
      description: 'Python functions, MCP integration, Code Interpreter',
      icon: <Wrench className="h-6 w-6" />,
      status: 'current',
      concepts: [
        'Tool registration and execution',
        'Python function tools',
        'MCP (Model Context Protocol) integration',
        'Hosted Code Interpreter',
        'External service integration via MCP',
        'Real-time data access through MCP tools'
      ],
      examples: [
        'Budget calculation with native Python tools',
        'Venue search using MCP external APIs',
        'Weather data integration for outdoor events',
        'Financial analysis with hosted code interpreter'
      ]
    },
    {
      id: 3,
      title: 'Multi-Agent',
      description: 'A2A communication, group discussion, task delegation',
      icon: <Users className="h-6 w-6" />,
      status: 'locked',
      concepts: [
        'Agent-to-Agent (A2A) communication patterns',
        'Real-time conversation flows between agents',
        'Task distribution and delegation strategies',
        'Consensus building and group decision making',
        'WebSocket-based live agent interactions',
        'Coordination strategies for complex workflows'
      ],
      examples: [
        'Live A2A communication in event planning',
        'Multi-agent group discussions with consensus',
        'Task delegation with specialized agent coordination',
        'Real-time workflow orchestration'
      ]
    },
    {
      id: 4,
      title: 'Workflows',
      description: 'Sequential, parallel, and conditional workflows',
      icon: <Workflow className="h-6 w-6" />,
      status: 'locked',
      concepts: [
        'Sequential workflow execution',
        'Parallel task processing',
        'Conditional branching',
        'Error handling and recovery'
      ],
      examples: [
        'Event planning pipeline',
        'Parallel venue and catering search',
        'Conditional approval workflows'
      ]
    },
    {
      id: 5,
      title: 'Orchestration',
      description: 'Magnetic patterns, adaptive coordination',
      icon: <Zap className="h-6 w-6" />,
      status: 'locked',
      concepts: [
        'Magnetic coordination patterns',
        'Adaptive agent coordination',
        'Dynamic resource allocation',
        'Complex workflow orchestration'
      ],
      examples: [
        'Dynamic agent assignment',
        'Load balancing across agents',
        'Adaptive workflow optimization'
      ]
    },
    {
      id: 6,
      title: 'Human-in-the-Loop',
      description: 'Approvals, feedback, interventions',
      icon: <HandHeart className="h-6 w-6" />,
      status: 'locked',
      concepts: [
        'Human approval workflows',
        'Feedback integration',
        'Intervention mechanisms',
        'Human-AI collaboration'
      ],
      examples: [
        'Budget approval gates',
        'Venue selection feedback',
        'Real-time plan adjustments'
      ]
    }
  ]

  const currentLevel = learningLevels.find(level => level.id === selectedLevel)
  const completedLevels = learningLevels.filter(level => level.status === 'completed').length
  const progressPercentage = (completedLevels / learningLevels.length) * 100

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Learning Progression</h1>
        <p className="text-xl text-muted-foreground">
          Master Microsoft Agent Framework through 6 progressive levels
        </p>
        <div className="max-w-md mx-auto space-y-2">
          <div className="flex justify-between text-sm">
            <span>Overall Progress</span>
            <span>{completedLevels}/{learningLevels.length} levels</span>
          </div>
          <Progress value={progressPercentage} className="w-full" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Learning Path</CardTitle>
              <CardDescription>
                Progress through each level to master agent orchestration
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {learningLevels.map((level) => (
                <Button
                  key={level.id}
                  variant={selectedLevel === level.id ? 'default' : 'ghost'}
                  className="w-full justify-start h-auto p-3"
                  onClick={() => setSelectedLevel(level.id)}
                  disabled={level.status === 'locked'}
                >
                  <div className="flex items-center space-x-3 w-full">
                    <div className="flex-shrink-0">
                      {level.status === 'completed' ? (
                        <CheckCircle className="h-5 w-5 text-green-500" />
                      ) : level.status === 'locked' ? (
                        <Lock className="h-5 w-5 text-muted-foreground" />
                      ) : (
                        level.icon
                      )}
                    </div>
                    <div className="flex-1 text-left">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Level {level.id}</span>
                        <Badge 
                          variant={
                            level.status === 'completed' ? 'default' : 
                            level.status === 'current' ? 'secondary' : 
                            'outline'
                          }
                          className="text-xs"
                        >
                          {level.status}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">{level.title}</p>
                    </div>
                    <ChevronRight className="h-4 w-4" />
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          {currentLevel && (
            <Card>
              <CardHeader>
                <div className="flex items-center space-x-3">
                  {currentLevel.icon}
                  <div>
                    <CardTitle>Level {currentLevel.id}: {currentLevel.title}</CardTitle>
                    <CardDescription>{currentLevel.description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <Tabs defaultValue="concepts" className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="concepts">Key Concepts</TabsTrigger>
                    <TabsTrigger value="examples">Examples</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="concepts" className="space-y-4">
                    <div className="grid gap-3">
                      {currentLevel.concepts.map((concept, index) => (
                        <Card key={index} className="p-3">
                          <div className="flex items-center space-x-2">
                            <div className="w-2 h-2 bg-primary rounded-full" />
                            <span className="text-sm">{concept}</span>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="examples" className="space-y-4">
                    <div className="grid gap-3">
                      {currentLevel.examples.map((example, index) => (
                        <Card key={index} className="p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">{example}</span>
                            <Button size="sm" variant="outline">
                              Try Example
                            </Button>
                          </div>
                        </Card>
                      ))}
                    </div>
                  </TabsContent>
                </Tabs>
                
                <div className="mt-6 flex space-x-3">
                  <Button 
                    className="flex-1"
                    disabled={currentLevel.status === 'locked'}
                  >
                    {currentLevel.status === 'completed' ? 'Review Level' : 'Start Learning'}
                  </Button>
                  {currentLevel.status === 'completed' && selectedLevel < learningLevels.length && (
                    <Button 
                      variant="outline"
                      onClick={() => setSelectedLevel(selectedLevel + 1)}
                    >
                      Next Level
                      <ChevronRight className="ml-2 h-4 w-4" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
