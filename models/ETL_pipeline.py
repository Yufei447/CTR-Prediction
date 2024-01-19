from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.ml.feature import StringIndexer, VectorAssembler, OneHotEncoder
from pyspark.ml import Pipeline
from pyspark.ml.functions import vector_to_array

spark = SparkSession.builder \
                    .appName("ctr prediction") \
                    .getOrCreate()

impression = spark.read.option('header', 'true') \
                       .option('inferSchema', 'true') \
                       .csv("/FileStore/tables/filtered_train.csv") \
                       .selectExpr("*", "substr(hour, 7) as hr") \
                       .drop('_c0')

impression = impression.withColumn('hr-app_category', F.concat('hr', 'app_category')) \
                       .withColumn('hr-site_category', F.concat('hr', 'site_category')) \
                       .withColumn('hr-device_type', F.concat('hr', 'device_type')) \
                       .withColumn('banner_pos-device_type', F.concat('banner_pos', 'device_type')) \
                       .withColumn('device_type-app_category', F.concat('device_type', 'app_category')) \
                       .withColumn('device_type-site_category', F.concat('device_type', 'site_category'))

strCols = map(lambda t: t[0], filter(lambda t: t[1] == 'string', impression.dtypes))
intCols = map(lambda t: t[0], filter(lambda t: t[1] == 'int', impression.dtypes))

strColsCount = sorted(map(lambda c: (c, impression.select(F.countDistinct(c)).collect()[0][0]), strCols), key=lambda x: x[1], reverse=True)
intColsCount = sorted(map(lambda c: (c, impression.select(F.countDistinct(c)).collect()[0][0]), intCols), key=lambda x: x[1], reverse=True)


maxBins = 100
wide_cols = list(map(lambda c: c[0], filter(lambda c: c[1] <= maxBins, strColsCount)))
wide_col_counts = list(map(lambda c: c[1], filter(lambda c: c[1] <= maxBins, strColsCount)))
wide_cols += list(map(lambda c: c[0], filter(lambda c: c[1] <= maxBins, intColsCount)))
wide_col_counts += list(map(lambda c: c[1], filter(lambda c: c[1] <= maxBins, intColsCount)))
wide_cols.remove('click')
wide_col_counts = sum(wide_col_counts) - 2 - len(wide_cols)  

embed_cols = [('device_model', impression.select('device_model').distinct().count(), 256),
              ('app_id', impression.select('app_id').distinct().count(), 256),
              ('site_id', impression.select('site_id').distinct().count(), 256),
              ('site_domain', impression.select(
                  'site_domain').distinct().count(), 256),
              ('app_domain', impression.select(
                  'app_domain').distinct().count(), 128),
              ]
strIndexers_wide = list(map(lambda c: StringIndexer(inputCol=c, outputCol=c+'_idx'), wide_cols))

embed_features = map(lambda c: c[0] + 'SEP' +str(c[1]) + 'SEP' + str(c[2]), embed_cols)
strIndexers_embed = list(map(lambda c: StringIndexer(inputCol=c[0], outputCol=c[0] + 'SEP' + str(c[1]) + 'SEP' + str(c[2])), embed_cols))
oneHotEncoders = list(map(lambda c: OneHotEncoder(inputCol=c+'_idx', outputCol=c+'_onehot'), wide_cols))
vectorAssembler = VectorAssembler(inputCols=list(map(lambda c: c+'_onehot', wide_cols)), outputCol='wide_features_v')
labelStringIndexer = StringIndexer(inputCol="click", outputCol="label")
stages = strIndexers_wide + strIndexers_embed + \
    oneHotEncoders + [vectorAssembler, labelStringIndexer]

# Create pipeline
pipeline = Pipeline(stages=stages)
featurizer = pipeline.fit(impression)

# dataframe with feature and intermediate transformation columns appended
featurizedImpressions = featurizer.transform(impression) \
                                  .withColumn('wide_features', vector_to_array('wide_features_v'))

train, test = featurizedImpressions.select([F.col('wide_features')[i] for i in range(wide_col_counts)] + ['label'] + list(embed_features)) \
                                   .randomSplit([0.7, 0.3], 42)




