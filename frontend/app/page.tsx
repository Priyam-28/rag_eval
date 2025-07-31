"use client";

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Upload, FileText, Brain, CheckCircle, AlertCircle } from 'lucide-react';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';

type Question = {
  id: string;
  question: string;
  expected_answer?: string;
};

type Answer = {
  question: string;
  answer: string;
  confidence?: number;
};

type ScoredAnswer = {
  question: string;
  expected_answer: string;
  rag_answer: string;
  score: number;
  status: 'excellent' | 'good' | 'poor';
};

export default function Home() {
  const [activeTab, setActiveTab] = useState('rag');
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [questionsFile, setQuestionsFile] = useState<File | null>(null);
  const [expectedAnswersFile, setExpectedAnswersFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [ragResults, setRagResults] = useState<Answer[]>([]);
  const [scoringResults, setScoringResults] = useState<ScoredAnswer[]>([]);

  const handlePdfUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
    }
  };

  const handleQuestionsUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/json') {
      setQuestionsFile(file);
    }
  };

  const handleExpectedAnswersUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/json') {
      setExpectedAnswersFile(file);
    }
  };

  const processRAG = async () => {
    if (!pdfFile || !questionsFile) return;

    setLoading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('pdf', pdfFile);
      formData.append('questions', questionsFile);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch('http://localhost:8000/process-rag', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.ok) {
        const results = await response.json();
        setRagResults(results.answers);
      } else {
        console.error('RAG processing failed');
      }
    } catch (error) {
      console.error('Error processing RAG:', error);
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  const processScoring = async () => {
    if (!questionsFile || !expectedAnswersFile) return;

    setLoading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('questions', questionsFile);
      formData.append('expected_answers', expectedAnswersFile);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 15, 90));
      }, 300);

      const response = await fetch('http://localhost:8000/score-answers', {
        method: 'POST',
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      if (response.ok) {
        const results = await response.json();
        setScoringResults(results.scored_answers);
      } else {
        console.error('Scoring failed');
      }
    } catch (error) {
      console.error('Error processing scoring:', error);
    } finally {
      setLoading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getStatusIcon = (status: string) => {
    if (status === 'excellent') return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (status === 'good') return <AlertCircle className="w-4 h-4 text-yellow-600" />;
    return <AlertCircle className="w-4 h-4 text-red-600" />;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-slate-900 mb-2">PDF RAG Intelligence</h1>
          <p className="text-slate-600 text-lg">Upload PDFs, ask questions, and score your AI responses</p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-2 h-12">
            <TabsTrigger value="rag" className="flex items-center gap-2">
              <Brain className="w-4 h-4" />
              RAG Q&A
            </TabsTrigger>
            <TabsTrigger value="scoring" className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4" />
              Answer Scoring
            </TabsTrigger>
          </TabsList>

          <TabsContent value="rag" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    Upload Files
                  </CardTitle>
                  <CardDescription>
                    Upload your PDF document and questions JSON file
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">PDF Document</label>
                    <input
                      type="file"
                      accept=".pdf"
                      onChange={handlePdfUpload}
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {pdfFile && (
                      <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {pdfFile.name}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Questions JSON</label>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleQuestionsUpload}
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                    {questionsFile && (
                      <p className="text-sm text-green-600 mt-1 flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {questionsFile.name}
                      </p>
                    )}
                  </div>

                  <Button 
                    onClick={processRAG} 
                    disabled={!pdfFile || !questionsFile || loading}
                    className="w-full"
                  >
                    {loading ? 'Processing...' : 'Generate Answers'}
                  </Button>

                  {loading && (
                    <div className="space-y-2">
                      <Progress value={progress} className="w-full" />
                      <p className="text-sm text-slate-600 text-center">Processing documents...</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>JSON Format Examples</CardTitle>
                  <CardDescription>Expected format for your input files</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-medium text-sm mb-2">Questions JSON:</h4>
                    <pre className="bg-slate-100 p-3 rounded-lg text-xs overflow-x-auto">
{`{
  "questions": [
    {
      "id": "1",
      "question": "What is the main topic?"
    },
    {
      "id": "2", 
      "question": "Who are the authors?"
    }
  ]
}`}
                    </pre>
                  </div>
                </CardContent>
              </Card>
            </div>

            {ragResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Answers</CardTitle>
                  <CardDescription>AI-generated responses based on your PDF</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {ragResults.map((result, index) => (
                      <div key={index} className="border rounded-lg p-4 bg-white">
                        <h4 className="font-medium text-slate-900 mb-2">Q: {result.question}</h4>
                        <p className="text-slate-700 leading-relaxed">{result.answer}</p>
                        {result.confidence && (
                          <Badge variant="secondary" className="mt-2">
                            Confidence: {(result.confidence * 100).toFixed(1)}%
                          </Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="scoring" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Upload className="w-5 h-5" />
                    Upload Test Files
                  </CardTitle>
                  <CardDescription>
                    Upload questions and expected answers for scoring
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Questions JSON</label>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleQuestionsUpload}
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Expected Answers JSON</label>
                    <input
                      type="file"
                      accept=".json"
                      onChange={handleExpectedAnswersUpload}
                      className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                    />
                  </div>

                  <Button 
                    onClick={processScoring} 
                    disabled={!questionsFile || !expectedAnswersFile || loading}
                    className="w-full"
                  >
                    {loading ? 'Scoring...' : 'Score Answers'}
                  </Button>

                  {loading && (
                    <div className="space-y-2">
                      <Progress value={progress} className="w-full" />
                      <p className="text-sm text-slate-600 text-center">Comparing answers...</p>
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Expected Answers Format</CardTitle>
                  <CardDescription>JSON structure for answer comparison</CardDescription>
                </CardHeader>
                <CardContent>
                  <pre className="bg-slate-100 p-3 rounded-lg text-xs overflow-x-auto">
{`{
  "answers": [
    {
      "id": "1",
      "question": "What is the main topic?",
      "expected_answer": "The document discusses..."
    },
    {
      "id": "2",
      "question": "Who are the authors?",
      "expected_answer": "John Doe and Jane Smith"
    }
  ]
}`}
                  </pre>
                </CardContent>
              </Card>
            </div>

            {scoringResults.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle className="w-5 h-5" />
                    Scoring Results
                  </CardTitle>
                  <CardDescription>
                    Comparison between expected and AI-generated answers
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {scoringResults.map((result, index) => (
                      <div key={index} className="border rounded-lg p-6 bg-white">
                        <div className="flex items-start justify-between mb-4">
                          <h4 className="font-medium text-slate-900 flex-1">Q: {result.question}</h4>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(result.status)}
                            <Badge className={getScoreColor(result.score)}>
                              {(result.score * 100).toFixed(1)}%
                            </Badge>
                          </div>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <h5 className="font-medium text-sm text-slate-600 mb-2">Expected Answer:</h5>
                            <p className="text-sm text-slate-700 bg-green-50 p-3 rounded border-l-4 border-green-200">
                              {result.expected_answer}
                            </p>
                          </div>
                          <div>
                            <h5 className="font-medium text-sm text-slate-600 mb-2">RAG Answer:</h5>
                            <p className="text-sm text-slate-700 bg-blue-50 p-3 rounded border-l-4 border-blue-200">
                              {result.rag_answer}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    <Separator />
                    
                    <div className="bg-slate-50 p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Overall Performance</h4>
                      <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                          <p className="text-2xl font-bold text-green-600">
                            {scoringResults.filter(r => r.status === 'excellent').length}
                          </p>
                          <p className="text-sm text-slate-600">Excellent (≥80%)</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-yellow-600">
                            {scoringResults.filter(r => r.status === 'good').length}
                          </p>
                          <p className="text-sm text-slate-600">Good (60-79%)</p>
                        </div>
                        <div>
                          <p className="text-2xl font-bold text-red-600">
                            {scoringResults.filter(r => r.status === 'poor').length}
                          </p>
                          <p className="text-sm text-slate-600">Poor (60%)</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}