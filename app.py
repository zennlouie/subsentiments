import panel as pn
import subprocess
import matplotlib.pyplot as plt
import pandas as pd
import time
import asyncpraw
import asyncio
from wordcloud import WordCloud
from reportlab.pdfgen import canvas


reddit = asyncpraw.Reddit(   
    client_id='E8v7MjxWvHIUjx4heL5g8g',      
    client_secret='5cCyUqml_aCgI7O9s_lhj4tUc5Irew',  
    user_agent='Test Scraper by u/azwischenzug'    
)

def download_pdf():
    return "sentiment_analysis_results.pdf"

js_refresh = """
window.location.reload();
"""

css = """
.scrollable-column {
    overflow-y: auto;
}

.bk-panel-models-layout-Column {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    width: 100vw;
}

.bk-input-container {
    width: 25vw;
    display: flex;
    justify-content: center;
}

.bk-input-group{
    align-items: center;

}
h1{
    font-size: 2em;
}

.bk-clearfix {
    margin-top: 10px; /* Adjust this value as needed */
    font-weight:bold;
}

.estimateed-time {
     style='font-weight:bold;'
}

.testt {
    margin-top: 15px;
    margin-right: 10px;
}
"""
async def get_values():
    subreddit_name = subreddit_input.value.lower()

    if isinstance(layout[-1], pn.pane.HTML):
        error_pane = layout[-1]
        layout.remove(error_pane)

    if subreddit_name.startswith("/r/"):
        subreddit_name = subreddit_name[3:]
    elif subreddit_name.startswith("r/"):
        subreddit_name = subreddit_name[2:]
    elif subreddit_name.startswith("reddit.com/r/"):
        subreddit_name = subreddit_name[13:]
    elif subreddit_name.startswith("www.reddit.com/r/"):
        subreddit_name = subreddit_name[17:]
    elif subreddit_name.startswith("https://www.reddit.com/r/"):
        subreddit_name = subreddit_name[26:]
    if not subreddit_name:
        error_message = "<h3 style='color:red;'>Please enter a subreddit name</h3>"
        error_pane = pn.pane.HTML(error_message, align="center")
        layout.append(error_pane)
        return
    try:
        subreddit = await reddit.subreddit(subreddit_name, fetch=True)
    except Exception as e:
        error_message = f"<h3 style='color:red;'>Subreddit '{subreddit_name}' does not exist</h3>"
        error_pane = pn.pane.HTML(error_message, align="center")
        layout.append(error_pane)
        return
    
    
    else:
        error_pane = layout[-1]
        layout.remove(error_pane)
        
    comments_posts = comments_posts_radio.value
    
    top_latest = top_latest_radio.value

    if date_range_radio.disabled:
        date_range = 0
    else:
        date_range = date_range_radio.value

    num_posts = num_posts_input.value
    num_comments = num_comments_input.value

    if comments_posts == "Posts + Comments":
        estimate1 = 4 * num_posts
        estimate2 = (num_posts * 5 + num_posts) / 100 * 45

    else:
        estimate1 = 1.5 * num_posts
        estimate2 = num_posts / 100 * 45
    
    if translation_radio.value == "Translate":
        translate = "True"
    else:
        translate = "False"
    
    return subreddit_name, comments_posts, top_latest, date_range, num_posts, num_comments, translate, estimate1, estimate2

async def perform_analysis(event):
    start_time = time.time()

    values = await get_values()
    
    script_names = ["data_gatherer.py", "labeler.py"]
    subreddit_name, comments_posts, top_latest, date_range, num_posts, num_comments, translate, estimate1, estimate2 = values
    data_gatherer_args = [subreddit_name, comments_posts, top_latest, date_range, num_posts, num_comments, translate]
    labeler_args = [subreddit_name, f'{subreddit_name}_data_gathered_cleaned.csv']
    args = [data_gatherer_args, labeler_args]
    progress_bar = pn.widgets.Progress(active=True, width=200, height=50, value=0, align="center")
    layout.append(progress_bar)

    await run_scripts(script_names, args, progress_bar, estimate1, estimate2)
    
    visualize_data(visualization_radio.value, f'{subreddit_name}_labeled.csv', subreddit_name)
    end_time = time.time()
    print("Time taken: ", end_time - start_time)

def visualize_data(values, file_path, subreddit_name):
    data = pd.read_csv(file_path)
    sentiment_map = {0: "Negative", 1: "Neutral", 2: "Positive"}
    data["Sentiment"] = data["Sentiment"].map(sentiment_map)
    data["text"] = data["text"].astype(str)

    loading = pn.indicators.LoadingSpinner(value=True, size=20, name='Visualizing Data and Making PDF...', align="center")
    layout.append(loading)
    
    sentiment_counts = data["Sentiment"].value_counts()
    total_count = len(data)
    positive_count = sentiment_counts.get("Positive", 0)
    negative_count = sentiment_counts.get("Negative", 0)
    neutral_count = sentiment_counts.get("Neutral", 0)
    positive_percentage = (positive_count / total_count) * 100
    negative_percentage = (negative_count / total_count) * 100
    neutral_percentage = (neutral_count / total_count) * 100
    date_range = pd.to_datetime(data['date']).min(), pd.to_datetime(data['date']).max()
    overall_sentiment = data["Sentiment"].mode()[0]

    c = canvas.Canvas("sentiment_analysis_results.pdf")
    c.setFont("Helvetica-Bold", 14)
    c.drawString(100, 800, f"Sentiment Analysis Results for /r/{subreddit_name}")
    c.setFont("Helvetica", 14)
    c.drawString(100, 780, f"Number of Posts/Comments: {len(data)}")
    c.drawString(100, 760, f"Date Range: {date_range[0]} - {date_range[1]}")
    c.drawString(100, 740, f"Negative Sentiment: {negative_percentage:.2f}% ({negative_count}/{total_count})")
    c.drawString(100, 720, f"Neutral Sentiment: {neutral_percentage:.2f}% ({neutral_count}/{total_count})")
    c.drawString(100, 700, f"Positive Sentiment: {positive_percentage:.2f}% ({positive_count}/{total_count})")
    c.drawString(100, 680, f"Overall Sentiment: {overall_sentiment}")

    panes = []
    image_files = []
    
    color = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}
    if "Bar Chart" in values:
        bar_chart = data['Sentiment'].value_counts().plot(kind='bar', title="Sentiment Distribution",  rot=0, color = [color[key] for key in data['Sentiment'].value_counts().index])
        plt.savefig('bar_chart.png')
        plt.close()
        bar_chart_pane = pn.pane.PNG('bar_chart.png', width=500, height=500)
        image_files.append('bar_chart.png')
        panes.append(bar_chart_pane)
        c.drawImage('bar_chart.png', 50, 200, width=500)
        c.showPage()
        
    if "Line Graph" in values:
        data['date'] = pd.to_datetime(data['date'])
        line_graph = data.groupby(data['date'].dt.date)['Sentiment'].value_counts().unstack().fillna(0)
        line_graph.plot(kind='line', title="Sentiment Over Time")
        plt.savefig('line_graph.png')
        plt.close()
        line_graph_pane = pn.pane.PNG('line_graph.png', width=500, height=500)
        panes.append(line_graph_pane)
        image_files.append('line_graph.png')
        c.drawImage('line_graph.png',  50, 200, width=500)
        c.showPage()

    if "Word Cloud" in values:
        word_cloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(data["text"]))
        plt.imshow(word_cloud)
        plt.axis('off')
        plt.savefig('word_cloud.png')
        plt.close()
        word_cloud_pane = pn.pane.PNG('word_cloud.png', width=500, height=500)  
        panes.append(word_cloud_pane)
        c.drawImage('word_cloud.png',  50, 200, width=500)
        c.showPage()

    if "Pie Graph" in values:
        pie_chart = data['Sentiment'].value_counts().plot(kind='pie', title="Sentiment Distribution")
        plt.savefig('pie_chart.png')
        plt.close()
        pie_chart_pane = pn.pane.PNG('pie_chart.png')
        panes.append(pie_chart_pane)
        c.drawImage('pie_chart.png',  50, 200, width=500)
        c.showPage()
    
    c.save()
    
    if panes:
        grid = pn.GridSpec(sizing_mode="stretch_both", max_height=1000, ncols=2, align="center")
        for i, pane in enumerate(panes):
            row = i // 2
            col = i % 2
            grid[row, col] = pane

    
    data_pane = pn.pane.DataFrame(data, width=800, height=200, align="center")
    layout.remove(loading)
    
    layout.clear()
     
    if overall_sentiment == "Negative":
        overall_sentiment_text = "<p style='color: red; font-weight:bold;'>Overall Sentiment: Negative</p>"
    elif overall_sentiment == "Neutral":
        overall_sentiment_text = "<p style='color: gray; font-weight:bold;'>Overall Sentiment: Neutral</p>"
    elif overall_sentiment == "Positive":
        overall_sentiment_text = "<p style='color: green; font-weight:bold;'>Overall Sentiment: Positive</p>"
    header = f"<h3 style='font-weight:bold;'>Sentiment Analysis Results for /r/{subreddit_name}\n</h3><p>Date Range: {date_range[0]} - {date_range[1]}</p><p>Negative Sentiment: {negative_percentage:.2f}% ({negative_count}/{total_count}\n)</p><p>Positive Sentiment: {positive_percentage:.2f}% ({positive_count}/{total_count})\n</p><p>Neutral Sentiment: {neutral_percentage:.2f}%({neutral_count}/{total_count})\n</p>{overall_sentiment_text}"
    refresh_button = pn.widgets.Button(name="<", button_type="primary", width=50, sizing_mode="fixed", css_classes=["testt"])
    refresh_button.js_on_click(code=js_refresh)
    layout.append(pn.Row(refresh_button, pn.pane.HTML(header), align="center"))
    download_button = pn.widgets.FileDownload(
        filename="sentiment_analysis_results.pdf",
        label="Download PDF",
        button_type="success",
        callback=download_pdf,
    )
    layout.append(pn.Row(download_button, align="center"))
    if panes:
        layout.append(grid)
    layout.append(data_pane)

async def run_python_script(script_name, args, progress_bar, estimate1, estimate2):
    parameter = ["python", script_name] + args.split(", ")
    
    if script_name == "data_gatherer.py":
        loading = pn.indicators.LoadingSpinner(value=True, size=20, name='Fetching and cleaning data from Reddit...', align="center")
    else:
        loading = pn.indicators.LoadingSpinner(value=True, size=20, name='Performing Sentiment Analysis...', align="center")

    layout.append(loading)
    progress_bar.value = progress_bar.value + 33
    process = await asyncio.create_subprocess_exec(*parameter)
    await process.wait()
    layout.remove(loading)
    
async def run_scripts(script_names, args, progress_bar, estimate1, estimate2):
    args = [', '.join(map(str, inner_list)) for inner_list in args]

    for i, script_name in enumerate(script_names):
        await run_python_script(script_name, args[i], progress_bar, estimate1, estimate2)

        if i == len(script_names) - 1:
            progress_bar.value = 100
            layout.remove(progress_bar) 
            analysis_done = "<h3 style='color:green;'>Analysis Done!</h3>"
            analysis_pane = pn.pane.HTML(analysis_done, align="center")
            layout.append(analysis_pane)


def toggle_p_tag(event):
    p_tag_row.height = 0 if p_tag.visible else 100
    p_tag.visible = not p_tag.visible

def open_modal(event):
    modal.open()
    
header = "<h1>SubSentiments: Reddit Sentiment Analysis Tool</h1>"
subreddit_input = pn.widgets.TextInput(placeholder="Enter Subreddit Name e.g Philippines, /r/Philippines, reddit.com/r/Philippines")
num_posts_input = pn.widgets.IntInput(name="# of Posts:", value=50, start=1, end=100, width=100, description="1-100 Posts only due to limitations")
num_comments_input = pn.widgets.IntInput(name="# of Comments:", value=5, start=1, end=10, width=100, description='1-10 Comments per post only due to limitations')
text = pn.widgets.StaticText(value=f"Estimated: 335.00 seconds", css_classes=["estimated-time"])
loading = pn.indicators.LoadingSpinner(value=True, size=20, name='Performing Sentiment Analysis...')
comments_posts_radio = pn.widgets.RadioButtonGroup(options=["Posts + Comments", "Posts only"], value="Posts + Comments", button_type="primary", button_style="outline")
top_latest_radio = pn.widgets.RadioButtonGroup(options=["Top Posts", "Latest Posts"], value="Top Posts", button_type="primary", button_style="outline")
date_range_radio = pn.widgets.RadioButtonGroup(options=["Last 24 Hours", "Last Week", "Last Month", "Last Year", "All Time"], value="All Time", button_type="primary", button_style="outline")
translation_radio = pn.widgets.RadioButtonGroup(options=["Translate", "Don't Translate"], value="Don't Translate", button_type="primary", button_style="outline")
visualize_text = "<h3>Choose the type/s of visualization you want to see</h3>"
table_radio = pn.widgets.RadioButtonGroup(options=["Data Table"], value="Data Table", disabled=True, button_type="primary", button_style="outline", description="Always on")
visualization_radio = pn.widgets.CheckButtonGroup(options=["Bar Chart", "Line Graph", "Word Cloud", "Pie Graph"], button_type="primary", button_style="outline")
analysis_button = pn.widgets.Button(name="Perform Sentiment Analysis", button_type="success", width=200, height=50)
modal_button = pn.widgets.Button(name="?", button_type="primary")
p_tag = pn.pane.HTML("<p>This tool perform Sentiment Analysis on posts/comments on the specified subreddit by the user. It will categorize the posts/comments gathered to negative, neutral, and positive. The user is given several options to suit their analysing needs. The user is also given options to choose the graphs they want to see. At the end, a download button is available to download the results of the analysis. It utilizes a DistilBERT model that has been fine-tuned and k-fold cross validated using a Reddit dataset with 55,000+ entries. The model currently being used has an accuracy of 77%.</p>", width=800, height=100, align="center")
p_tag.visible = False
p_tag_row = pn.Row(p_tag, align="center",height=0)
modal_button.on_click(toggle_p_tag)

def update_date_range(event):
    if top_latest_radio.value == "Latest Posts":
        date_range_radio.disabled = True
    else:
        date_range_radio.disabled = False

def update_text(event):
    num_posts = num_posts_input.value
    if comments_posts_radio.value == "Posts + Comments":
        estimate1 = 4 * num_posts
        estimate2 = (num_posts * 5 + num_posts) / 100 * 45
        sum = estimate1 + estimate2
        
    else:
        estimate1 = 0.1 * num_posts
        estimate2 = num_posts / 100 * 45
        sum = estimate1 + estimate2
    text.value = f"Estimated: {sum:.2f} seconds"
    
    
def update_comment_posts(event):
    update_text(event)

def stop_execution(event):
    global running
    running = False

comments_posts_radio.param.watch(update_comment_posts, 'value')
top_latest_radio.param.watch(update_date_range, 'value')
num_posts_input.param.watch(update_text, 'value')
analysis_button.on_click(perform_analysis)
running = True
layout = pn.Column(
    pn.Row(pn.Spacer(width=10), pn.pane.HTML(header), modal_button, align="center"), 
    p_tag_row,
    pn.Row(subreddit_input, align="center"),  
    pn.Row(num_posts_input, num_comments_input, text, align="center"),
    pn.Row(top_latest_radio, comments_posts_radio, align="center"),  
    pn.Row(date_range_radio, align="center"),
    pn.Row(translation_radio, align="center"),
    pn.Row(visualize_text, align="center"),
    pn.Row(table_radio, visualization_radio, align="center"),
    pn.Row(analysis_button, align="center"),
    sizing_mode="stretch_both",
    height_policy="max",
    css_classes=["scrollable-column"],
)
pn.extension(raw_css=[css])

layout.servable("SubSentiments")