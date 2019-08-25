from datetime import datetime
from plotly.subplots import make_subplots
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import functools


def show_or_return(graph_func):
    """
    decorator for functions that can either 
    return a graph object or show a figure
    """
    @functools.wraps(graph_func)
    def wrapper(*args, **kwargs):
        fig, graph = graph_func(*args, **kwargs)
        if kwargs.get('show', True):
            fig.show()
        else:
            return graph
    return wrapper


class ChatStat:
    """
    container for chat and messages dataframe with functions
    to generate statistics

    Parameters
    ----------
    chat_df: pandas.DataFrame
        dataframe containing chat information
    msg_df: pandas.DataFrame
        dataframe containing message information

    """

    def __init__(self, chat_df, msg_df):
        self.chat_df = chat_df
        self.msg_df = msg_df

    def print_df(self):
        """ prints both dataframes """
        print("------ CHATS DATAFRAME ------")
        print(self.chat_df)
        print("------ MESSAGES DATAFRAME ------")
        print(self.msg_df)

    @show_or_return
    def biggest_chat(self, top=10, kind="pie", show=True):
        """ 
        plots the largest chats overall. by default, only plots top 10

        Parameters
        ----------
        top: int, default=10
            limits the plot to `top` number of chats
        kind: str in {'pie', 'bar'}
            kind of chart to plot, pie or bar
        show: bool, default=True
            toggle to show fig instead of returning graph obj

        Returns
        -------
        plotly.graph_objects
            graph object (Bar or Pie)
        """
        count_df = self.msg_df.groupby("thread_path").count()
        count_df.sort_values("msg", inplace=True, ascending=False)
        count_df = count_df[:top]
        count_df = count_df.join(self.chat_df)
        if kind == "pie":
            graph = go.Pie(labels=count_df.title, values=count_df.msg)
            fig = go.Figure(graph)
        elif kind == "bar":
            graph = go.Bar(x=count_df.title, y=count_df.msg)
            fig = go.Figure(graph)
            fig.update_layout(xaxis=go.layout.XAxis(title=go.layout.xaxis.Title(text="Chat")),
                              yaxis=go.layout.YAxis(title=go.layout.yaxis.Title(text="Number of Messages")))
        else:
            raise ValueError("kind must be either 'pie' or 'bar'")
        fig.update_layout(title_text=f"Top {top} largest chats")
        return fig, graph

    @show_or_return
    def sent_from(self, chat=None, top=10, omit_first=False, kind="pie", show=True):
        """ 
        plots the number of messages received based on sender for the DF passed in. 
        Can be used on filtered DataFrames. by default, only plots top 10 senders

        Parameters
        ----------
        chat: pandas.DataFrame
            message DataFrame to plot from, if none is provided, use self.msg_df
        top: int, default=10
            limits the plot to `top` number of chats
        omit_first: bool, default=False
            toggle to omit the first largest chat, which is typically the user
        kind: str in {'pie', 'bar'}
            kind of chart to plot, pie or bar
        show: bool, default=True
            toggle to show fig instead of returning graph obj

        Returns
        -------
        plotly.graph_objects
            graph object (Bar or Pie)
        """
        chat = chat or self.msg_df
        start = int(omit_first)
        count_df = chat.groupby("sender").count()
        count_df.sort_values("msg", inplace=True, ascending=False)
        count_df = count_df[start:top]
        count_df = count_df.join(self.chat_df)
        if kind == "pie":
            graph = go.Pie(labels=count_df.index, values=count_df.msg)
            fig = go.Figure(graph)
        elif kind == "bar":
            graph = go.Bar(x=count_df.index, y=count_df.msg)
            fig = go.Figure(graph)
            fig.update_layout(xaxis=go.layout.XAxis(title=go.layout.xaxis.Title(text="Sender")),
                              yaxis=go.layout.YAxis(title=go.layout.yaxis.Title(text="Number of Messages")))
        else:
            raise ValueError("kind must be either 'pie' or 'bar'")
        fig.update_layout(title_text=f"Messages by Sender (top {top})")
        return fig, graph

    @show_or_return
    def msg_types(self, chat=None, show=True):
        """ 
        Takes a filtered msg_df (based on sender or chat title) and breaks down the type of messages 

        Parameters
        ----------
        chat: pandas.DataFrame
            message DataFrame to plot from, if none is provided, use self.msg_df
        show: bool, default=True
            toggle to show fig instead of returning graph obj

        Returns
        -------
        plotly.graph_objects.Pie
            a Pie graph object
        """
        chat = chat or self.msg_df
        type_dict = {"type": {"stickers": chat.sticker.count(), "photos": chat.photos.count(), "videos": chat.videos.count(), "links": chat[[("http" in str(msg)) for msg in chat.msg]].msg.count()}}
        type_df = pd.DataFrame(type_dict)
        graph = go.Pie(labels=type_df.index, values=type_df.type, textinfo='label+percent', showlegend=False)
        fig = go.Figure(graph)
        fig.update_layout(title_text="Types of Multimedia Used")
        return fig, graph

    @show_or_return
    def chat_types(self, chat=None, show=True):
        """ 
        Takes a filtered msg_df (based on sender or chat title) and breaks down the type of chat 

        Parameters
        ----------
        chat: pandas.DataFrame
            message DataFrame to plot from, if none is provided, use self.msg_df
        show: bool, default=True
            toggle to show fig instead of returning graph obj

        Returns
        -------
        plotly.graph_objects.Pie
            a Pie graph object
        """
        messages = chat or self.msg_df
        grouped = messages.groupby("thread_path").count().join(self.chat_df).groupby("thread_type").sum()
        graph = go.Pie(labels=grouped.index, values=grouped.msg, textinfo='label+percent', showlegend=False)
        fig = go.Figure(graph)
        fig.update_layout(title_text="Types of Chat")
        return fig, graph

    def personal_stats(self, name):
        """ 
        Plots a bunch of different plots based on a fitlered DataFrame of messages from `name`

        Parameters
        ----------
        name: str
            name of sender to filter for

        Returns
        -------
        plotly.graph_objects.Figure
            a Figure object with personal stats
        """
        from_sender = self.msg_df[self.msg_df['sender'] == name]
        print("Total # of messages: %d" % from_sender.msg.size)

        if from_sender.empty:
            print("Could not find any messages from %s" % name)
            return ""

        chat_count = from_sender.groupby("thread_path").count()
        chat_count = chat_count.join(self.chat_df)
        total_msg = chat_count["msg"].sum()
        chat_count['proportion'] = chat_count["msg"] / total_msg
        full = chat_count.loc[:, ["title", "proportion"]].set_index("title").sort_values('proportion', ascending=False)
        if full.size > 6:
            pie = full[:5]
            pie = pie.append(pd.DataFrame([['others', 1 - sum(pie.proportion)]], columns=['title', 'proportion']).set_index('title'))
        else:
            pie = full

        fig, proportions = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))
        fig.suptitle("Where are %s's messages going?" % name, fontsize=20)
        pie.plot(ax=proportions[0], kind='pie', y='proportion', legend=False, labeldistance=0.2, rotatelabels=True).set_ylabel("")
        proportions[1].axis('off')
        full = (full * 100).round(4)[:20]
        proportions[1].table(cellText=full.values, rowLabels=full.index, loc='right', colLabels=["percentage"], colWidths=[0.2]).scale(1.2, 1.2)

        _, pieax = plt.subplots(nrows=1, ncols=2, figsize=(20, 10))
        self.msg_types(from_sender, pieax[0])
        self.chat_types(from_sender, pieax[1])
        self.time_stats(from_sender)
        self.word_counts(from_sender)

    def stat_by_chat(self, chat):
        """ Plots a bunch of different plots based on a fitlered DataFrame of messages in the chat `chat` """
        thread = self.chat_df[self.chat_df.title == chat].index[0]
        from_chat = self.msg_df[self.msg_df.thread_path == thread]
        print("Total # of messages: %d" % from_chat.msg.size)
        self.sent_from(from_chat, top=10)
        self.msg_types(from_chat, fsize=(8, 8))
        self.time_stats(from_chat)
        self.word_counts(from_chat)

    def generate_time_indexed_df(self, messages):
        """
        turns a message df to a time-indexed df with columns for
        year, month, hour and minute

        Parameters
        ----------
        messages: pandas.DataFrame
            message DataFrame to plot from

        Returns
        -------
        pandas.DataFrame
            time-indexed DF for time-based stats
        """
        time_indexed = messages.set_index('timestamp')
        time_indexed['year'] = time_indexed.index.year
        time_indexed['month'] = time_indexed.index.strftime("%b")
        time_indexed['hour'] = time_indexed.index.hour
        time_indexed['minute'] = time_indexed.index.minute

        return time_indexed

    def yearly_graph(self, time_indexed):
        """
        generates an aggregated message count by year

        Parameters
        ----------
        time_indexed: pandas.DataFrame
            time-indexed message DataFrame to plot from
            (use `generate_time_indexed_df`)

        Returns
        -------
        plotly.graph_objects.Bar
            Bar plot of data
        """
        yearly_df = time_indexed.groupby("year").count()
        yearly_graph = go.Bar(x=yearly_df.index, y=yearly_df.msg)
        return yearly_graph

    def hourly_graph(self, time_indexed):
        """
        generates an aggregated message count by hour

        Parameters
        ----------
        time_indexed: pandas.DataFrame
            time-indexed message DataFrame to plot from
            (use `generate_time_indexed_df`)

        Returns
        -------
        plotly.graph_objects.Bar
            Bar plot of data
        """
        hourly_df = time_indexed.groupby("hour").count()
        hourly_df['hour_str'] = [datetime.strptime(str(hour), '%H').strftime("%I %p") for hour in hourly_df.index]
        hourly_graph = go.Bar(x=hourly_df.hour_str, y=hourly_df.msg)
        return hourly_graph

    def monthly_graph(self, time_indexed):
        """
        generates an aggregated message count by month

        Parameters
        ----------
        time_indexed: pandas.DataFrame
            time-indexed message DataFrame to plot from
            (use `generate_time_indexed_df`)

        Returns
        -------
        plotly.graph_objects.Bar
            Bar plot of data
        """
        monthly_df = time_indexed.groupby("month").count()
        monthly_df = monthly_df.reindex(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
        monthly_graph = go.Bar(x=monthly_df.index, y=monthly_df.msg)
        return monthly_graph

    def minutely_graph(self, time_indexed):
        """
        generates an aggregated message count by minute

        Parameters
        ----------
        time_indexed: pandas.DataFrame
            time-indexed message DataFrame to plot from
            (use `generate_time_indexed_df`)

        Returns
        -------
        plotly.graph_objects.Bar
            Bar plot of data
        """
        minutely_df = time_indexed.groupby("minute").count()
        minutely_graph = go.Bar(x=minutely_df.index, y=minutely_df.msg)
        return minutely_graph

    def time_stats(self, messages=None):
        """ 
        Plots the time-based activity of the passed in DataFrame
        or all messages available

        Parameters
        ----------
        messages: pandas.DataFrame
            message DataFrame to plot from, if none is provided, use self.msg_df

        Returns
        -------
        plotly.graph_objects.Figure
            a plotly Figure object with time-based stats in a 4x4 grid

        """
        messages = messages or self.msg_df
        # fig.suptitle("Time-based Stats: Procrastination Metrics", fontsize=20)
        time_indexed = self.generate_time_indexed_df(messages)
        yearly_graph = self.yearly_graph(time_indexed)
        monthly_graph = self.monthly_graph(time_indexed)
        hourly_graph = self.hourly_graph(time_indexed)
        minutely_graph = self.minutely_graph(time_indexed)

        when = make_subplots(rows=2, cols=2, specs=[[{"type": "bar"}] * 2] * 2,
                             subplot_titles=['Yearly', 'Monthly', 'Hourly', 'Minute-by-Minute'])
        when.add_trace(yearly_graph, row=1, col=1)
        when.add_trace(monthly_graph, row=1, col=2)
        when.add_trace(hourly_graph, row=2, col=1)
        when.add_trace(minutely_graph, row=2, col=2)
        when.update_layout(height=950, width=950, title_text="Time-based Metrics", showlegend=False)

        return when

    def word_counts(self, chat, lengths=[1, 3, 5, 7], top=10):
        """ Counts the word usage based on the passed in DataFrame `chat` and plots words that are longer than `lengths` """
        messages = chat.msg
        words = {'count': {}}
        for msg in messages:
            msg = str(msg).encode('latin1').decode('utf8')  # need this to get around encoding problems
            for word in msg.split(" "):
                word = word.lower()
                word = word.rstrip('?:!.,;')
                if word in words['count']:
                    words['count'][word] += 1
                else:
                    words['count'][word] = 1

        word_df = pd.DataFrame(words).sort_values("count", ascending=False)
        num_plots = len(lengths)
        numrows = num_plots // 2 + num_plots % 2
        fig, ax = plt.subplots(nrows=numrows, ncols=2, figsize=(16, 5 * numrows))
        if num_plots % 2 != 0:
            if numrows > 1:
                ax[numrows - 1][1].axis("off")
            else:
                ax[1].axis("off")
        fig.suptitle("Word Counts", fontsize=20)
        plot_index = 0

        def create_word_df(l):
            len_bool = [(len(word) >= l) for word in word_df.index]
            df = word_df[len_bool][:top]
            return df

        for l in lengths:
            r = plot_index // 2
            c = 0 if plot_index % 2 == 0 else 1
            plot_index += 1
            if numrows > 1:
                create_word_df(l).plot(ax=ax[r][c], kind="bar", y="count", legend=False, rot=50, title="Top words %d letters or more" % l)
            else:
                create_word_df(l).plot(ax=ax[c], kind="bar", y="count", legend=False, rot=50, title="Top words %d letters or more" % l)

    @show_or_return
    def chat_counts(self, top=10, omit_first=True, show=True):
        """ 
        counts the number of chats each person is in and plots the top x people in the most chats 

        Parameters
        ----------
        top: int, default=10
            limits the plot to `top` number of people
        omit_first: bool, default=True
            toggle to omit the first largest value, which is typically the user
        show: bool, default=True
            toggle to show fig instead of returning graph obj

        Returns
        -------
        plotly.graph_objects.Bar or None
            Bar graph depicting chat counts

        """
        start = int(omit_first)
        counts = self.msg_df.groupby(["sender", "thread_path"]).size().reset_index().groupby("sender").count().sort_values('thread_path', ascending=False)
        counts = counts[start:top]
        graph = go.Bar(x=counts.index, y=counts.thread_path)
        fig = go.Figure(graph)
        fig.update_layout(title_text=f"Number of chats by person (Top {top})")
        return fig, graph


if __name__ == "__main__":
    import loader

    stat = ChatStat(*loader.load_from_csv())
    stat.personal_stats("Dilip Rathinakumar")
