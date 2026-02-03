import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Check, ChevronRight, Building2, FileText, FolderKanban, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card'
import { OrganizationStep } from './steps/OrganizationStep'
import { ImportPapersStep } from './steps/ImportPapersStep'
import { CreateProjectStep } from './steps/CreateProjectStep'
import { ScorePaperStep } from './steps/ScorePaperStep'

export interface OnboardingState {
  organizationType: string
  importedPaperIds: string[]
  projectId: string | null
  scoredPaperId: string | null
}

const steps = [
  {
    id: 'organization',
    title: 'Organization Setup',
    description: 'Tell us about your organization',
    icon: Building2,
  },
  {
    id: 'import',
    title: 'Import Papers',
    description: 'Add your first research papers',
    icon: FileText,
  },
  {
    id: 'project',
    title: 'Create Project',
    description: 'Set up your first pipeline',
    icon: FolderKanban,
  },
  {
    id: 'score',
    title: 'Score a Paper',
    description: 'Get AI-powered insights',
    icon: Sparkles,
  },
]

interface OnboardingWizardProps {
  onComplete: () => void
}

export function OnboardingWizard({ onComplete }: OnboardingWizardProps): JSX.Element {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(0)
  const [state, setState] = useState<OnboardingState>({
    organizationType: '',
    importedPaperIds: [],
    projectId: null,
    scoredPaperId: null,
  })

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      onComplete()
    }
  }

  const handleSkip = () => {
    handleNext()
  }

  const handleComplete = () => {
    onComplete()
    navigate('/dashboard')
  }

  const updateState = (updates: Partial<OnboardingState>) => {
    setState((prev) => ({ ...prev, ...updates }))
  }

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <OrganizationStep
            value={state.organizationType}
            onChange={(type) => updateState({ organizationType: type })}
            onNext={handleNext}
          />
        )
      case 1:
        return (
          <ImportPapersStep
            importedIds={state.importedPaperIds}
            onImport={(ids) => updateState({ importedPaperIds: [...state.importedPaperIds, ...ids] })}
            onNext={handleNext}
            onSkip={handleSkip}
          />
        )
      case 2:
        return (
          <CreateProjectStep
            projectId={state.projectId}
            onProjectCreated={(id) => updateState({ projectId: id })}
            onNext={handleNext}
            onSkip={handleSkip}
          />
        )
      case 3:
        return (
          <ScorePaperStep
            paperIds={state.importedPaperIds}
            onScored={(id) => updateState({ scoredPaperId: id })}
            onComplete={handleComplete}
            onSkip={handleComplete}
          />
        )
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted/50 flex items-center justify-center p-4">
      <div className="w-full max-w-4xl">
        {/* Progress Steps */}
        <div className="mb-8">
          <nav aria-label="Progress">
            <ol className="flex items-center justify-center space-x-2">
              {steps.map((step, index) => {
                const StepIcon = step.icon
                const isCompleted = index < currentStep
                const isCurrent = index === currentStep

                return (
                  <li key={step.id} className="flex items-center">
                    <div
                      className={cn(
                        'flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors',
                        isCompleted && 'bg-primary border-primary text-primary-foreground',
                        isCurrent && 'border-primary text-primary',
                        !isCompleted && !isCurrent && 'border-muted-foreground/30 text-muted-foreground/50'
                      )}
                    >
                      {isCompleted ? (
                        <Check className="h-5 w-5" />
                      ) : (
                        <StepIcon className="h-5 w-5" />
                      )}
                    </div>
                    {index < steps.length - 1 && (
                      <ChevronRight
                        className={cn(
                          'h-5 w-5 mx-2',
                          index < currentStep ? 'text-primary' : 'text-muted-foreground/30'
                        )}
                      />
                    )}
                  </li>
                )
              })}
            </ol>
          </nav>
          <div className="text-center mt-4">
            <h2 className="text-sm font-medium text-muted-foreground">
              Step {currentStep + 1} of {steps.length}
            </h2>
          </div>
        </div>

        {/* Step Content */}
        <Card className="shadow-lg">
          <CardHeader className="text-center pb-2">
            <CardTitle className="text-2xl">{steps[currentStep].title}</CardTitle>
            <CardDescription className="text-base">
              {steps[currentStep].description}
            </CardDescription>
          </CardHeader>
          <CardContent className="pt-6">{renderStep()}</CardContent>
        </Card>

        {/* Skip All */}
        {currentStep < steps.length - 1 && (
          <div className="text-center mt-6">
            <Button variant="ghost" onClick={handleComplete} className="text-muted-foreground">
              Skip onboarding and go to dashboard
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
