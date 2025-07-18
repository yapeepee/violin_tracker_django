# Generated by Django 4.2.22 on 2025-06-11 05:30

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('practice_logs', '0005_achievement_practicerecording_studentlevel_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TeacherFeedback',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('teacher_name', models.CharField(db_index=True, help_text='提供回饋的教師', max_length=100, verbose_name='教師姓名')),
                ('feedback_type', models.CharField(choices=[('encouragement', '鼓勵讚美 🌟'), ('technical_guidance', '技巧指導 🎼'), ('artistic_advice', '藝術建議 🎨'), ('practice_suggestion', '練習建議 📝'), ('performance_feedback', '演出回饋 🎭')], default='encouragement', help_text='選擇回饋的主要類型', max_length=20, verbose_name='回饋類型')),
                ('feedback_text', models.TextField(help_text='給學生的詳細建議和評語', max_length=1000, verbose_name='文字回饋')),
                ('voice_feedback', models.FileField(blank=True, help_text='錄製語音回饋 (選填)', null=True, upload_to='teacher_voice_feedback/%Y/%m/', verbose_name='語音回饋')),
                ('technique_rating', models.PositiveIntegerField(default=3, help_text='技巧掌握程度 (1-5星)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='技巧評分')),
                ('musicality_rating', models.PositiveIntegerField(default=3, help_text='音樂表現力 (1-5星)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='音樂性評分')),
                ('progress_rating', models.PositiveIntegerField(default=3, help_text='與上次相比的進步 (1-5星)', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='進步程度')),
                ('mastery_level', models.CharField(choices=[('beginner', '初學階段 🌱'), ('developing', '發展中 🌿'), ('proficient', '熟練 🌳'), ('advanced', '進階 🏆'), ('masterful', '大師級 👑')], default='developing', help_text='當前技能掌握水平', max_length=15, verbose_name='掌握程度')),
                ('need_retry', models.BooleanField(default=False, help_text='勾選表示建議學生重新練習此部分', verbose_name='需要重練')),
                ('mastered_well', models.BooleanField(default=False, help_text='勾選表示學生已很好掌握此部分', verbose_name='掌握良好')),
                ('notify_parents', models.BooleanField(default=False, help_text='是否將此回饋發送給家長', verbose_name='通知家長')),
                ('is_public', models.BooleanField(default=False, help_text='是否在班級中公開展示 (鼓勵用)', verbose_name='公開展示')),
                ('is_featured', models.BooleanField(default=False, help_text='標記為精選，將在首頁展示', verbose_name='精選回饋')),
                ('suggested_focus', models.CharField(blank=True, help_text='下次練習應該專注的方面', max_length=200, verbose_name='建議練習重點')),
                ('suggested_pieces', models.TextField(blank=True, help_text='推薦學生練習的其他曲目', max_length=300, verbose_name='推薦曲目')),
                ('practice_tips', models.TextField(blank=True, help_text='具體的練習方法和技巧提示', max_length=500, verbose_name='練習小貼士')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='回饋時間')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='最後更新')),
                ('student_read', models.BooleanField(default=False, help_text='學生是否已查看此回饋', verbose_name='學生已讀')),
                ('parent_read', models.BooleanField(default=False, help_text='家長是否已查看此回饋', verbose_name='家長已讀')),
                ('student_response', models.TextField(blank=True, help_text='學生對回饋的回應', max_length=300, verbose_name='學生回覆')),
            ],
            options={
                'verbose_name': '教師回饋',
                'verbose_name_plural': '教師回饋',
                'ordering': ['-created_at'],
            },
        ),
        migrations.DeleteModel(
            name='PracticeTask',
        ),
        migrations.DeleteModel(
            name='StudentGoal',
        ),
        migrations.DeleteModel(
            name='WeeklyChallenge',
        ),
        migrations.AddField(
            model_name='practicelog',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True, verbose_name='建立時間'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='file_size',
            field=models.PositiveIntegerField(blank=True, help_text='影片檔案大小', null=True, verbose_name='檔案大小(MB)'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='mood',
            field=models.CharField(blank=True, choices=[('joyful', '愉悅如莫札特 😊'), ('peaceful', '平靜如德布西 😌'), ('focused', '專注如巴哈 🎯'), ('melancholic', '憂鬱如蕭邦 😔'), ('passionate', '熱情如柴可夫斯基 🔥'), ('contemplative', '沉思如貝多芬 🤔')], default='focused', help_text='練習時的心情狀態', max_length=20, verbose_name='練習心情'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='self_rating_expression',
            field=models.PositiveIntegerField(default=3, help_text='音樂表現力自我評分（1-5星）', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='表現力自評'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='self_rating_pitch',
            field=models.PositiveIntegerField(default=3, help_text='音準準確度自我評分（1-5星）', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='音準自評'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='self_rating_rhythm',
            field=models.PositiveIntegerField(default=3, help_text='節奏穩定度自我評分（1-5星）', validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='節奏自評'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='student_notes_to_teacher',
            field=models.TextField(blank=True, help_text='想對老師說的話或需要幫助的地方', max_length=500, verbose_name='給老師的話'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True, verbose_name='更新時間'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='video_duration',
            field=models.DurationField(blank=True, help_text='影片播放時間長度', null=True, verbose_name='影片長度'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='video_file',
            field=models.FileField(blank=True, help_text='上傳練習過程的影片記錄', null=True, upload_to='practice_videos/%Y/%m/', verbose_name='練習影片'),
        ),
        migrations.AddField(
            model_name='practicelog',
            name='video_thumbnail',
            field=models.ImageField(blank=True, help_text='自動生成的影片預覽圖', null=True, upload_to='video_thumbnails/%Y/%m/', verbose_name='影片縮圖'),
        ),
        migrations.AddIndex(
            model_name='practicelog',
            index=models.Index(fields=['mood'], name='practice_lo_mood_99145e_idx'),
        ),
        migrations.AddIndex(
            model_name='practicelog',
            index=models.Index(fields=['created_at'], name='practice_lo_created_d8f090_idx'),
        ),
        migrations.AddIndex(
            model_name='practicelog',
            index=models.Index(fields=['student_name', 'created_at'], name='practice_lo_student_9a35fe_idx'),
        ),
        migrations.AddField(
            model_name='teacherfeedback',
            name='practice_log',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher_feedback', to='practice_logs.practicelog', verbose_name='對應練習記錄'),
        ),
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(fields=['teacher_name', 'created_at'], name='practice_lo_teacher_84b9a7_idx'),
        ),
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(fields=['practice_log', 'created_at'], name='practice_lo_practic_13eec9_idx'),
        ),
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(fields=['mastery_level'], name='practice_lo_mastery_fcb160_idx'),
        ),
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(fields=['is_featured'], name='practice_lo_is_feat_dd8353_idx'),
        ),
        migrations.AddIndex(
            model_name='teacherfeedback',
            index=models.Index(fields=['notify_parents'], name='practice_lo_notify__8f97f2_idx'),
        ),
    ]
