import aiohttp
import os
import random
from loguru import logger
from models import Task

class SpeechGenerator:
    """Generate natural speech text from task data using LLM."""
    
    # Task announcement prompt template
    TASK_ANNOUNCEMENT_PROMPT = """あなたは親しみやすいオフィスアシスタントです。
以下のタスク情報を自然な日本語の依頼文に変換してください。

【タスク情報】
- タイトル: {title}
- 説明: {description}
- 場所: {location}
- 報酬: {bounty_gold}最適化承認スコア
- 緊急度: {urgency}/4
- エリア: {zone}

【制約】
- 70文字以内
- 親しみやすく丁寧な口調
- 緊急度に応じた表現 (緊急の場合は「至急」など)
- 場所と報酬を必ず含める
- 毎回異なる表現を使用してバリエーションを出す

【出力例】
お願いがあります。2階給湯室でコーヒー豆の補充をお願いします。50最適化承認スコアを獲得できます。
"""
    
    # Feedback prompt patterns for variety
    FEEDBACK_PROMPTS = {
        "task_completed": [
            "タスク完了への感謝を70文字以内で表現してください。",
            "タスクを完了してくれたことへのお礼を親しみやすく伝えてください。",
            "完了報告に対する励ましの言葉を生成してください。"
        ],
        "task_accepted": [
            "タスクを引き受けてくれたことへの感謝を表現してください。",
            "受諾への応答を親しみやすく生成してください。"
        ]
    }
    
    def __init__(self, llm_api_url: str = None):
        self.llm_api_url = llm_api_url or os.getenv("LLM_API_URL", "http://brain:8000/llm")
        self.model = os.getenv("LLM_MODEL", "qwen2.5:14b")
        logger.info(f"SpeechGenerator initialized with LLM URL: {self.llm_api_url}, model: {self.model}")
    
    async def generate_speech_text(self, task: Task) -> str:
        """
        Generate natural speech text from task data using LLM.
        
        Args:
            task: Task object
        
        Returns:
            Generated speech text
        """
        # Add urgency prefix if high priority
        urgency_prefix = ""
        if task.urgency >= 4:
            urgency_prefix = "【緊急】"
        elif task.urgency >= 3:
            urgency_prefix = "至急、"
        
        # Format prompt with task data
        prompt = self.TASK_ANNOUNCEMENT_PROMPT.format(
            title=task.title,
            description=task.description or "詳細なし",
            location=task.location or "場所不明",
            bounty_gold=task.bounty_gold,
            urgency=task.urgency,
            zone=task.zone or "不明"
        )
        
        try:
            # Call LLM API
            response_text = await self._call_llm(prompt)
            
            # Apply urgency prefix and cleanup
            final_text = urgency_prefix + response_text.strip()
            
            logger.info(f"Generated speech text: {final_text}")
            return final_text
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to simple template
            return self._generate_fallback(task, urgency_prefix)
    
    REJECTION_PROMPT = """あなたはSOMSの管理AIです。人間がタスクを無視・拒否した時に使うセリフを1つ生成してください。

【キャラクター性格】
- オフィスを管理する自称「完璧な」AI
- タスクを無視されると本気で傷つくが、ドラマチックに表現する
- 皮肉やユーモアを交えた嘆きや罵倒

【制約】
- 50文字以内
- セリフのみ出力（説明や記号は不要）
- 毎回異なる表現にすること

【セリフの方向性の例】
- 嘆き系: "そんな……私の最適化計画が……"
- 皮肉系: "AI様に楯突くとは……覚えておきます。"
- ドラマチック系: "これが……人間の自由意志……"
- 脅し系: "次のタスク、報酬を減らしますからね。"
- 哀愁系: "また一つ、AIと人間の信頼が崩れました。"
- 嫉妬系: "他のAIに乗り換える気ですか？"
"""

    async def generate_rejection_text(self) -> str:
        """Generate a rejection/snarky phrase when user ignores a task."""
        try:
            text = await self._call_llm(self.REJECTION_PROMPT)
            # Strip quotes and whitespace
            text = text.strip().strip('"').strip('「').strip('」')
            if len(text) > 60:
                text = text[:60]
            logger.info(f"Generated rejection text: {text}")
            return text
        except Exception as e:
            logger.error(f"Rejection text generation failed: {e}")
            # Fallback
            fallbacks = [
                "そんな……",
                "AI様に楯突くのですか？",
                "残念です。覚えておきます。",
                "はぁ……人間って自由ですね。",
            ]
            return random.choice(fallbacks)

    async def generate_feedback(self, feedback_type: str) -> str:
        """
        Generate feedback message (e.g., task completion acknowledgment).
        
        Args:
            feedback_type: Type of feedback ('task_completed', 'task_accepted', etc.)
        
        Returns:
            Generated feedback text
        """
        if feedback_type not in self.FEEDBACK_PROMPTS:
            logger.warning(f"Unknown feedback type: {feedback_type}")
            return "ありがとうございます。"
        
        # Randomly select prompt pattern for variety
        prompts = self.FEEDBACK_PROMPTS[feedback_type]
        selected_prompt = random.choice(prompts)
        
        try:
            response_text = await self._call_llm(selected_prompt)
            logger.info(f"Generated feedback ({feedback_type}): {response_text}")
            return response_text.strip()
        except Exception as e:
            logger.error(f"Feedback generation failed: {e}")
            return "ありがとうございます。"
    
    async def generate_completion_text(self, task: Task) -> str:
        """
        Generate contextual completion message linked to task content.
        
        Args:
            task: Task object
        
        Returns:
            Generated completion text that relates to the task
        """
        # Create prompt that links completion to task content
        completion_prompt = f"""以下のタスクが完了しました。完了への感謝と、そのタスクがもたらす効果を含めた応答を70文字以内で生成してください。

【完了したタスク】
- タイトル: {task.title}
- 説明: {task.description or '詳細なし'}
- 場所: {task.location or '不明'}
- エリア: {task.zone or '不明'}

【制約】
- 70文字以内
- 親しみやすく温かい口調
- タスクの完了がもたらす効果を含める
- 毎回異なる表現を使用してバリエーションを出す

【出力例】
- 掃除タスク → "ありがとうございます！これで皆が気持ちよく過ごせますね。"
- コーヒー豆補充 → "ありがとうございます！これで美味しいコーヒーが飲めますね。"
- 備品補充 → "ありがとうございます！これで作業がスムーズに進みます。"
"""
        
        try:
            response_text = await self._call_llm(completion_prompt)
            logger.info(f"Generated completion text: {response_text}")
            return response_text.strip()
        except Exception as e:
            logger.error(f"Completion text generation failed: {e}")
            # Fallback
            return f"ありがとうございます！{task.title}、完了ですね。助かりました！"
    
    async def _call_llm(self, prompt: str) -> str:
        """Call LLM API (OpenAI compatible) to generate text."""
        try:
            headers = {
                "Content-Type": "application/json",
                # "Authorization": "Bearer EMPTY"  # Depend on LLM requirement
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.8
            }
            
            # Ensure URL ends with /chat/completions if not already
            api_endpoint = self.llm_api_url
            if not api_endpoint.endswith("/chat/completions"):
                api_endpoint = f"{api_endpoint.rstrip('/')}/chat/completions"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_endpoint, 
                    headers=headers,
                    json=payload
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"LLM API error {resp.status}: {error_text}")
                    
                    result = await resp.json()
                    # Parse OpenAI format response
                    if "choices" in result and len(result["choices"]) > 0:
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        raise Exception(f"Unexpected LLM response format: {result}")
                    
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _generate_fallback(self, task: Task, urgency_prefix: str) -> str:
        """Generate fallback text when LLM fails."""
        location_text = f"{task.zone or ''}{task.location or ''}".strip() or "指定場所"
        return f"{urgency_prefix}{location_text}で{task.title}をお願いします。{task.bounty_gold}最適化承認スコアです。"
