import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from './ui/card'
import { Checkbox } from './ui/checkbox'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { Wrench, Globe, MapPin, Cloud, Calculator, Database, Search, BarChart } from 'lucide-react'

interface McpTool {
  name: string
  description: string
  icon: React.ReactNode
  category: 'venue' | 'weather' | 'data' | 'external' | 'calculation'
  enabled: boolean
}

interface McpToolSelectorProps {
  onToolChange: (tools: string[]) => void
}

const availableMcpTools: McpTool[] = [
  {
    name: 'venue_search',
    description: 'Search for event venues using external databases and APIs',
    icon: <MapPin className="h-4 w-4" />,
    category: 'venue',
    enabled: true
  },
  {
    name: 'weather_api',
    description: 'Get weather forecasts for outdoor events and backup planning',
    icon: <Cloud className="h-4 w-4" />,
    category: 'weather',
    enabled: true
  },
  {
    name: 'budget_calculator',
    description: 'Advanced financial calculations and cost optimization tools',
    icon: <Calculator className="h-4 w-4" />,
    category: 'calculation',
    enabled: true
  },
  {
    name: 'vendor_database',
    description: 'Access external vendor databases and rating systems',
    icon: <Database className="h-4 w-4" />,
    category: 'external',
    enabled: false
  },
  {
    name: 'market_research',
    description: 'Real-time market data for pricing and availability',
    icon: <BarChart className="h-4 w-4" />,
    category: 'data',
    enabled: false
  },
  {
    name: 'location_search',
    description: 'Geographic and demographic analysis for event locations',
    icon: <Search className="h-4 w-4" />,
    category: 'external',
    enabled: false
  }
]

const categoryColors = {
  venue: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
  weather: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
  data: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200',
  external: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200',
  calculation: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
}

export function McpToolSelector({ onToolChange }: McpToolSelectorProps) {
  const [tools, setTools] = useState<McpTool[]>(availableMcpTools)

  const handleToolToggle = (toolName: string, checked: boolean) => {
    const updatedTools = tools.map(tool => 
      tool.name === toolName ? { ...tool, enabled: checked } : tool
    )
    setTools(updatedTools)
    
    const enabledTools = updatedTools.filter(tool => tool.enabled).map(tool => tool.name)
    onToolChange(enabledTools)
  }

  const enabledCount = tools.filter(tool => tool.enabled).length
  const categories = [...new Set(tools.map(tool => tool.category))]

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <Wrench className="h-5 w-5" />
            <span>MCP Tools</span>
          </CardTitle>
          <Badge variant="secondary">
            {enabledCount} enabled
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Model Context Protocol tools extend agent capabilities with external services
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {categories.map(category => (
          <div key={category} className="space-y-3">
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className={categoryColors[category as keyof typeof categoryColors]}>
                {category.charAt(0).toUpperCase() + category.slice(1)}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {tools.filter(tool => tool.category === category).length} tools
              </span>
            </div>
            
            <div className="space-y-2 ml-4">
              {tools
                .filter(tool => tool.category === category)
                .map(tool => (
                  <div key={tool.name} className="flex items-start space-x-3 p-3 rounded-lg border">
                    <Checkbox
                      id={tool.name}
                      checked={tool.enabled}
                      onCheckedChange={(checked) => handleToolToggle(tool.name, checked as boolean)}
                      className="mt-1"
                    />
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center space-x-2">
                        {tool.icon}
                        <label 
                          htmlFor={tool.name}
                          className="text-sm font-medium cursor-pointer"
                        >
                          {tool.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </label>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {tool.description}
                      </p>
                    </div>
                  </div>
                ))}
            </div>
            
            {category !== categories[categories.length - 1] && <Separator />}
          </div>
        ))}
        
        <div className="mt-4 p-3 bg-muted rounded-lg">
          <div className="flex items-center space-x-2 mb-2">
            <Globe className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-medium">MCP Integration Status</span>
          </div>
          <p className="text-xs text-muted-foreground">
            {enabledCount > 0 
              ? `${enabledCount} MCP tools will be available to agents during event planning. Agents will automatically select appropriate tools based on task requirements.`
              : 'No MCP tools enabled. Agents will use only native capabilities.'
            }
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
