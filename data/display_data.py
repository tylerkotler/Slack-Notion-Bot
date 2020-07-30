from bokeh.plotting import figure, output_file, show, save, ColumnDataSource
from bokeh.models.tools import HoverTool
from bokeh.transform import factor_cmap
from bokeh.palettes import Blues8
from bokeh.embed import components, file_html
from bokeh.resources import CDN
import pandas as pd
import datetime
from string import Template
import sys, os
sys.path.append(os.path.realpath(".."))
from config import s3_key, s3_bucket, s3_secret
import boto3 
import io

s3 = boto3.client(
        's3',
        aws_access_key_id=s3_key,
        aws_secret_access_key=s3_secret
)

def scatter(status, furthest):
    
    if furthest == 'True':
        with open('status_times_furthest_condensed.csv', 'wb') as f:
            s3.download_fileobj(s3_bucket, 'status_times_furthest_condensed.csv', f)
        df = pd.read_csv('status_times_furthest_condensed.csv', sep="|")
        # obj = s3.get_object(Bucket=s3_bucket, Key='status_times_furthest_condensed.csv')
        # df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    else:
        with open('status_times_condensed.csv', 'wb') as f:
            s3.download_fileobj(s3_bucket, 'status_times_condensed.csv', f)
        df = pd.read_csv('status_times_condensed.csv', sep="|")
        # obj = s3.get_object(Bucket=s3_bucket, Key='status_times_condensed.csv')
        # df = pd.read_csv(io.BytesIO(obj['Body'].read()))
    # copy_df = df
    df['Ship Date']=pd.to_datetime(df['Ship Date'])
    df[status] = pd.to_numeric(df[status], downcast="float")
    # df.columns = df.iloc[0]

    source = ColumnDataSource(df)

    # output_file('templates/display-data.html')
    # output_file('scatter.html')

    # ship_date_list = source.data['Ship Date'].tolist()

    p = figure(
        x_axis_type='datetime',
        plot_width = 600,
        plot_height = 400,
        title=f'{status}',
        y_axis_label='Hours',
        tools="pan,box_select,zoom_in,zoom_out,save,reset"
    )

    p.scatter(
        y=status, 
        x='Ship Date',
        # fill_color = factor_cmap(
        #     'Car',
        #     palette=Blues8,
        #     factors=car_list
        # ),
        fill_alpha=0.5,
        source=source,
    )

    hover = HoverTool()
    html = """
        <div>
            <h4>@Story</h4>
            <div><strong>Ship Date: </strong>@{Ship Date}{%F}</div>
            <div><strong>Hours: </strong>@{$status}{%0.2f}</div>
        </div>
    """
    replaced_html = Template(html).safe_substitute(status=status)
    hover.tooltips = replaced_html

    hover.formatters = {
        "@{Ship Date}": "datetime",
        f"@\u007b{status}\u007d": "printf",

    }

    p.add_tools(hover)

    save(p)

    script, div = components(p)

    return script, div