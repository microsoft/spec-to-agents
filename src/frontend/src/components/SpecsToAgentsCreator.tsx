import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Badge } from './ui/badge'
import { Separator } from './ui/separator'
import { 
  Bot, 
  FileText, 
  Zap, 
  Download,
  Copy,
  CheckCircle
} from 'lucide-react'
import { toast } from 'sonner'

interface AgentSpec {
  name: string
  role: string
  capabilities: string[]
  instructions: string
  tools: string[]
}

export function SpecsToAgentsCreator() {
  const [agentName, setAgentName] = useState('')
  const [agentRole, setAgentRole] = useState('')
  const [agentCapabilities, setAgentCapabilities] = useState('')
  const [agentInstructions, setAgentInstructions] = useState('')
  const [agentTools, setAgentTools] = useState('')
  const [generatedSpec, setGeneratedSpec] = useState<AgentSpec | null>(null)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerateAgent = async () => {
    if (!agentName || !agentRole) {
      toast.error('Please provide at least agent name and role')
      return
    }

    setIsGenerating(true)
    
    try {
      await new Promise(resolve => setTimeout(resolve, 2000))
      
      const spec: AgentSpec = {
        name: agentName,
        role: agentRole,
        capabilities: agentCapabilities.split(',').map(c => c.trim()).filter(Boolean),
        instructions: agentInstructions || `You are ${agentName}, a specialized agent focused on ${agentRole}. Your primary responsibility is to assist users with tasks related to your expertise area.`,
        tools: agentTools.split(',').map(t => t.trim()).filter(Boolean)
      }
      
      setGeneratedSpec(spec)
      toast.success('Agent specification generated successfully!')
      
    } catch (error) {
      toast.error('Failed to generate agent specification')
    } finally {
      setIsGenerating(false)
    }
  }

  const handleCopySpec = () => {
    if (generatedSpec) {
      const specText = JSON.stringify(generatedSpec, null, 2)
      navigator.clipboard.writeText(specText)
      toast.success('Agent specification copied to clipboard!')
    }
  }

  const handleDownloadSpec = () => {
    if (generatedSpec) {
      const specText = JSON.stringify(generatedSpec, null, 2)
      const blob = new Blob([specText], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${generatedSpec.name.toLowerCase().replace(/\s+/g, '-')}-agent-spec.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      toast.success('Agent specification downloaded!')
    }
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-bold">Specs-to-Agents Creator</h1>
        <p className="text-xl text-muted-foreground">
          Generate specialized AI agents from specifications
        </p>
        <p className="text-sm text-muted-foreground max-w-2xl mx-auto">
          Define your agent requirements and automatically generate a complete agent specification 
          ready for deployment with the Microsoft Agent Framework.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <FileText className="h-5 w-5" />
              <span>Agent Specification</span>
            </CardTitle>
            <CardDescription>
              Define the characteristics and capabilities of your agent
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Agent Name *</label>
              <Input
                placeholder="e.g., Marketing Specialist, Data Analyst"
                value={agentName}
                onChange={(e) => setAgentName(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Primary Role *</label>
              <Input
                placeholder="e.g., Content creation and marketing strategy"
                value={agentRole}
                onChange={(e) => setAgentRole(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Key Capabilities</label>
              <Input
                placeholder="e.g., SEO optimization, social media, analytics (comma-separated)"
                value={agentCapabilities}
                onChange={(e) => setAgentCapabilities(e.target.value)}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Custom Instructions</label>
              <Textarea
                placeholder="Specific instructions for how the agent should behave..."
                value={agentInstructions}
                onChange={(e) => setAgentInstructions(e.target.value)}
                rows={4}
              />
            </div>
            
            <div className="space-y-2">
              <label className="text-sm font-medium">Required Tools</label>
              <Input
                placeholder="e.g., web_search, calculator, email_sender (comma-separated)"
                value={agentTools}
                onChange={(e) => setAgentTools(e.target.value)}
              />
            </div>
            
            <Button 
              onClick={handleGenerateAgent}
              disabled={isGenerating}
              className="w-full"
              size="lg"
            >
              {isGenerating ? (
                <>
                  <Bot className="mr-2 h-4 w-4 animate-spin" />
                  Generating Agent...
                </>
              ) : (
                <>
                  <Zap className="mr-2 h-4 w-4" />
                  Generate Agent Specification
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Bot className="h-5 w-5" />
              <span>Generated Agent</span>
            </CardTitle>
            <CardDescription>
              Your agent specification ready for deployment
            </CardDescription>
          </CardHeader>
          <CardContent>
            {generatedSpec ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">{generatedSpec.name}</h3>
                  <Badge variant="secondary">
                    <CheckCircle className="mr-1 h-3 w-3" />
                    Generated
                  </Badge>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">Role</h4>
                    <p className="text-sm">{generatedSpec.role}</p>
                  </div>
                  
                  {generatedSpec.capabilities.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground">Capabilities</h4>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {generatedSpec.capabilities.map((capability, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {capability}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div>
                    <h4 className="text-sm font-medium text-muted-foreground">Instructions</h4>
                    <p className="text-xs text-muted-foreground bg-muted p-2 rounded">
                      {generatedSpec.instructions}
                    </p>
                  </div>
                  
                  {generatedSpec.tools.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-muted-foreground">Tools</h4>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {generatedSpec.tools.map((tool, index) => (
                          <Badge key={index} variant="secondary" className="text-xs">
                            {tool}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                
                <Separator />
                
                <div className="flex space-x-2">
                  <Button onClick={handleCopySpec} variant="outline" size="sm" className="flex-1">
                    <Copy className="mr-2 h-3 w-3" />
                    Copy Spec
                  </Button>
                  <Button onClick={handleDownloadSpec} variant="outline" size="sm" className="flex-1">
                    <Download className="mr-2 h-3 w-3" />
                    Download
                  </Button>
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Bot className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Generate an agent specification to see the results here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
