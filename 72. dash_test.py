from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# 앱 생성/ 앱이름으로 __name__은 파일이름 그대로 가져옴
app = Dash(__name__)

# 레이아웃 정의
app.layout = html.Div([
    html.H4('Interactive scatter plot with Iris dataset'), 
    dcc.Graph(id="scatter-plot"), # 그래프
    html.P("Filter by petal width:"),
    dcc.RangeSlider( # 범위 조정하는 슬라이더
        id='range-slider',
        min=0, max=2.5, step=0.1,
        marks={0: '0', 2.5: '2.5'}, # 표시값
        value=[0.5, 2] # 초기 선택 값.
    ),
])


@app.callback(
    # 인풋들어오면 그래프 조정
    Output("scatter-plot", "figure"), 
    #사용자가 슬라이더를 조작하면 값이 바뀌어 콜백이 실행됨
    Input("range-slider", "value"))

# 슬라이더 값이 바뀔 때 실행되는 함수./ 콜백을 받아서 자동 작동
def update_bar_chart(slider_range): 
    df = px.data.iris() # replace with your own data source
    low, high = slider_range
    mask = (df['petal_width'] > low) & (df['petal_width'] < high)
    fig = px.scatter(
        df[mask], x="sepal_width", y="sepal_length",
        color="species", size='petal_length',
        hover_data=['petal_width'])
    return fig

# 서버 실행
app.run(debug=True) 
# 코드 변경 시 자동으로 리로드되고 에러 메시지도 상세히 표시

#python app.py