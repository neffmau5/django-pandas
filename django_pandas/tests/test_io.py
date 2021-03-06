from django.test import TestCase
import pandas as pd
import numpy as np
from .models import MyModel, Trader, Security, TradeLog, MyModelChoice
from django_pandas.io import read_frame


class IOTest(TestCase):

    def setUp(self):
        data = {
            'col1': np.array([1, 2, 3, 5, 6, 5, 5]),
            'col2': np.array([10.0, 2.4, 3.0, 5, 6, np.nan, 5]),
            'col3': np.array([9.5, 2.4, 3.0, 5, 6, 7.5, 2.5]),
            'col4': np.array([9, 2, 3, 5, 6, 7, 2]),
        }
        index = pd.Index(['a', 'b', 'c', 'd', 'e', 'f', 'h'])

        self.df = pd.DataFrame(index=index, data=data)

        for ix, cols in self.df.iterrows():
            MyModel.objects.create(
                index_col=ix,
                col1=cols['col1'],
                col2=cols['col2'],
                col3=cols['col3'],
                col4=cols['col4']
            )

    def test_basic(self):
        qs = MyModel.objects.all()
        df = read_frame(qs)
        n, c = df.shape
        self.assertEqual(n, qs.count())
        fields = MyModel._meta.get_all_field_names()
        self.assertEqual(c, len(fields))
        df1 = read_frame(qs, ['col1', 'col2'])
        self.assertEqual(df1.shape, (qs.count(), 2))

    def test_choices(self):

        MyModelChoice.objects.create(col1=1, col2=9999.99)
        MyModelChoice.objects.create(col1=2, col2=0.99)
        MyModelChoice.objects.create(col1=3, col2=45.6)
        MyModelChoice.objects.create(col1=2, col2=2.6)

        qs = MyModelChoice.objects.all()
        df = read_frame(qs, verbose=True)
        self.assertEqual(df.col1[0], 'First')
        self.assertEqual(df.col1[1], 'Second')
        self.assertEqual(df.col1[2], 'Third')
        self.assertEqual(df.col1[3], 'Second')
        df = read_frame(qs, verbose=False)
        self.assertEqual(df.col1[0], 1)
        self.assertEqual(df.col1[1], 2)
        self.assertEqual(df.col1[2], 3)
        self.assertEqual(df.col1[3], 2)

    def test_index(self):
        qs = MyModel.objects.all()
        df = read_frame(qs, ['col1', 'col2', 'col3', 'col4'],
                        index_col='index_col')
        self.assertEqual(df.shape, (qs.count(), 4))
        self.assertEqual(set(df.index.tolist()),
                         set(qs.values_list('index_col', flat=True)))


class RelatedFieldsTest(TestCase):
    def setUp(self):
        bob = Trader.objects.create(name="Jim Brown")
        fish = Trader.objects.create(name="Fred Fish")
        abc = Security.objects.create(symbol='ABC', isin='999901')
        zyz = Security.objects.create(symbol='ZYZ', isin='999901')
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T09:30:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T10:00:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T10:30:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=bob, symbol=abc,
                                log_datetime='2013-01-01T11:00:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T09:30:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T10:00:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T10:30:00',
                                price=30, volume=300)
        TradeLog.objects.create(trader=fish, symbol=zyz,
                                log_datetime='2013-01-01T11:00:00',
                                price=30, volume=300)

    def test_related(self):
        qs = TradeLog.objects.all()
        cols = ['log_datetime', 'symbol', 'symbol__isin', 'trader__name',
                'price', 'volume']
        df = read_frame(qs, cols)

        self.assertEqual(df.shape, (qs.count(), len(cols)))
