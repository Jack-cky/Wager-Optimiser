# J-League Prediction, YATTA! — Wager Optimisation on Asian Handicap with Machine Learning
<p align="center">
    <a href="https://bet.hkjc.com/football/index.aspx?lang=en"><img src="https://github.com/Jack-cky/JPY-Wager_Optimisation_on_Asian_Handicap_with_Machine_Learning/blob/main/imgs/surewin.png"></a><br>
    <i> Credit: <a href="https://www.donotgamble.org.hk/en/index.php"> The Ping Wo Fund </a></i>
</p>

---
### TL;DR
Used a random forest model (tuned with BayesSearchCV) to predict Asian handicap results on J1-League. The model achieved 64% accuracy and is expected to generate at least HKD 1,560 in 73 football matches.

<p align="center">
  <b>DISCLAIMER: THIS PROJECT DOES NOT ENCOURAGE ANY WAGER BEHAVIOUR</b>
</p>

---
### Repository Structure
```
J-League-Prediction-YATTA
|
└───data
|   |   fixtures.parquet            # normalised fixture records
|   |   j1_league_featured.parquet  # featured data
|   |   j1_league.parquet           # raw data
|   |   plays.parquet               # normalised play records
|
└───eda
|   |   eda.twbx  # Tableau workbook to verify opportunities
|
└───imgs
|   |   <images used on README.md>
|
└───src
|   |   01_web_scraping.ipynb         # ingest J1 league data from the Internet
|   |   02_data_preprocessing.ipynb   # cleanse and wrangle raw data
|   |   03_feature_engineering.ipynb  # create and explore explanatory variables
|   |   04_machine_learning.ipynb     # build and tune learning algorithms
|   |   05_model_evaluation.ipynb     # calculate profit and ROI
|
└───README.md  # you are here
|
└───requirements.txt  # dependencies used on the project
```

---
### Background
"_Small bet for entertainment, big bet become LI Ka Shing._" Wagering on a football match is REALLY exciting. You will never know the result until the last second. The hope and trust in your bet drive you crazy during the 2 hours. Over years of experience, we do not have any strategies for each bet but merely rely on feeling and belief. Approaching to 2022 FIFA World Cup, it has become a hot topic and triggered our motivation to build machine learning models and predict the results of football matches. Putting our expertise into the domain sounds interesting, and we kicked start the project in late October 2022.

---
### Data Source
As the title suggests, this project emphasises on J-League, in specific, J1 league season 2022 only. Because J-League is not as popular as other major football leagues, many data-providing websites do not have a complete set of records. Although the [official website](https://www.jleague.jp/match/) and the [Jockey Club](https://footylogic.com/en/tournament/league/50000009/standings) release match results, it does take time to programme a web scrapper. Fortunately, we found [TotalCorner](https://www.totalcorner.com) shares structured datasets for a variety of leagues with a user-friendly web design. Data is properly cleansed and wrangled for our experiments. We also translated our wager experience into additional features, which aimed to fit the models well.

Here we place some assumptions about the data
- data available on TotalCorner are valid and sound
- individual records are independent of each other (fundamental assumption of learning algorithms)

---
### Exploratory Data Analysis
With years of experience, we dare to say wager on [Asian handicap](https://is.hkjc.com/football/info/en/betting/bettypes_hdc.asp) (the handicap) is the trivial and the harshest option to generate profits. This project targets estimating the handicap results and optimises return on investment (ROI).

<p align="center">
    <a href="https://bet.hkjc.com/football/index.aspx?lang=en"><img src="https://github.com/Jack-cky/JPY-Wager_Optimisation_on_Asian_Handicap_with_Machine_Learning/blob/main/imgs/handicap.png"></a><br>
</p>

For dealer manipulation, the match results are adjusted after the addition of the handicap. The handicap shows the market attitude toward the games. Usually, the handicap would balance the final match results for the 2 playing teams. A half-half outcome is expected on the left-hand-side figure. Besides, teams playing in their stadium would feel more confident and usually outperform the other team. Hence, we can proxy the thinking of dealers when players on the home stadium. The figure on the right-hand side proves the ideas above.

<p align="center">
    <a href="https://bet.hkjc.com/football/index.aspx?lang=en"><img src="https://github.com/Jack-cky/JPY-Wager_Optimisation_on_Asian_Handicap_with_Machine_Learning/blob/main/imgs/stadium.png"></a><br>
</p>

With the supplement of the above figures, can we say that the effect of the home stadium is significant? We undergo several hypothesis tests on the belief. Unfortunately, there is a difference in the effect on the stadium but not significant (less the 5% of our test). Yet, we are not interested in the source of raw data. We worked out several net differences as input features, which improved the learning algorithm's performance.

---
### Model Building and Evaluation
To simulate the actual performance of model prediction, we split data into 2 portions where matches after September are considered production data and will be used to calculate ROI. We built 6 models on the project, including a distance-based model, linear models, ensemble tree models and a neural network model. To optimise the performance, we also tune the algorithms with several methodologies, such as `RandomisedSearchCV`, `BayesSearchCV`, `optuna` and `hyperopt`. Since the handicap (response variable) is almost balanced by nature under dealer manipulation, the objective of hyperparameter turning is to maximise accuracy.

| Model | ACCURACY | AUC | PARAMETERS |
| --- | --- | --- | --- |
| Random Forest (BayesSearchCV) | 0.643836 | 0.627112 | OrderedDict([('bootstrap', False), ('criterion... |
| Random Forest (Optuna) | 0.630137 | 0.610983 | {'bootstrap': False, 'criterion': 'entropy', '... |
| Random Forest | 0.616438 | 0.603303 | None |
| eXtreme Gradient Boosting (Optuna) | 0.616438 | 0.599078 | {'colsample_bytree': 0.38691249885012907, 'eva... |
| eXtreme Gradient Boosting (Hyperopt) | 0.616438 | 0.569508 | {'colsample_bytree': 0.34187263717236394, 'eva... |

As shown above, ensemble tree models outperform production data while achieving at least 60% accuracy, which beats random guesses. After training the models, it remains 73 games to make wagers. Random Forest with BayesSearchCV (the model) generates at least HKD 1,560 (minimum HKD 200 per bet), which attains 29% ROI. Within 2 months (until the end of the season), the model yielded a positive return with proof of production data. However, we cannot conclude a success for the project and will explain it in the next section.

---
### Defect and Brainstorm
Outsider matches are not uncommon in any league. No one knows a game will be an outsider, even dealers, and sometimes it does not really make any sense. For [example](https://www.jleague.jp/match/j1/2022/101203/live/#teamdata), the match was about Yokohama F-Marinos (first in ranking) and Jubilo Iwata (last in ranking). Dealers thought Yokohama F-Marinos should be winning the game and gave a negative handicap to the team. It turned out Jubilo Iwata beats Yokohama F-Marinos.

<p align="center">
    <a href="https://bet.hkjc.com/football/index.aspx?lang=en"><img src="https://github.com/Jack-cky/JPY-Wager_Optimisation_on_Asian_Handicap_with_Machine_Learning/blob/main/imgs/outsider.png" height="400px"></a><br>
    <i> Credit: <a href="https://www.jleague.jp/match/j1/2022/101203/live/#teamdata"> jleague.jp </a></i>
</p>

<pre>
<b>Model Prediction:
index    date          home                  away            handicap    results    net_goals    y_hat</b>
2432     2022-10-12    Yokohama F-Marinos    Jubilo Iwata    -2.0        0          -1           1
</pre>

Our model also thinks that Yokohama F-Marinos should win the game, shown in `y_hat`. Because these events happen sometimes, there is no golden rule to predict the outcome. In other words, it is almost impossible and very difficult for learning algorithms to generalise the pattern, which is also the limit of the project.

We found this problem occurs every season, and fail to train any model at a large scale. We consider the situation as data drifting over time. Under error analysis, experts (we) even fail to make a good sense of the prediction. We rely on the wager strategies and try to bet on different combinations to generate profit. The model we built in the project failed to be put into production in long run, which is the reason why we do not consider it a success for the project.

After hundreds of experiment loops, we achieved around 80% accuracy _IF WE CAN PREDICT THE MACHE RESULT CORRECTLY_. It sounds really unfeasible and unrealistic to make 100% accuracy on game results, but we may obtain a 60% to 80% accuracy model on the handicap if we could do well on predicting the game results with at least a 70% score of matrics. 

---
### Acknowledgements
- discussion on sport even prediction on [Low classification accuracy, what to do next?](https://stats.stackexchange.com/questions/38218/low-classification-accuracy-what-to-do-next)
- ideas of tuning hyperparameter is referenced from [Hyperparameter Optimization of Machine Learning Algorithms](https://github.com/LiYangHart/Hyperparameter-Optimization-of-Machine-Learning-Algorithms)

---
### License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/Jack-cky/JPY-Wager_Optimisation_on_Asian_Handicap_with_Machine_Learning/blob/main/LICENSE) file for details.
