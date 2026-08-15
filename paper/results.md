# Confirmatory results (school-clustered SEs)

Clusters: 15; seasons: [2021, 2022, 2023, 2024]; star-depth r=0.840

Delta AIC vs best: {'controls': 19.682808876973894, 'star': 8.136500557867635, 'depth': 0.0, 'pack_gap': 16.732625575536957, 'star_gap': 0.8154925456257445, 'both': 0.8154925456257445, 'wcac': 2.6770949582367507}

Holdout by model: {'controls': {'n': 12, 'rmse': 3.075035726360041, 'mae': 2.5582201890471343, 'spearman': 0.6783216783216784}, 'star': {'n': 12, 'rmse': 3.3267851729156233, 'mae': 2.432580682297028, 'spearman': 0.7832167832167832}, 'depth': {'n': 12, 'rmse': 3.514580921297109, 'mae': 3.0225916158250463, 'spearman': 0.8671328671328673}, 'pack_gap': {'n': 12, 'rmse': 2.5341335377013885, 'mae': 2.023723710791672, 'spearman': 0.7622377622377624}, 'star_gap': {'n': 12, 'rmse': 3.7275562199485117, 'mae': 3.2275848132080736, 'spearman': 0.8741258741258742}, 'both': {'n': 12, 'rmse': 3.727556219948548, 'mae': 3.2275848132081144, 'spearman': 0.8741258741258742}, 'wcac': {'n': 12, 'rmse': 3.7268682844860836, 'mae': 3.2562636451464524, 'spearman': 0.9230769230769231}}

LOO school depth coef: {'n': 15, 'mean': 3.840191778424588, 'min': 3.253648613163384, 'max': 4.609221014908367}

LOO season RMSE: {'2021': 2.019057522334056, '2022': 1.2898746644899686, '2023': 2.2275880148946, '2024': 3.7183924628736875}

Permutation: {'observed': 0.6888564591293008, 'p': 0.005} {'observed': 0.07018711649686982, 'p': 0.33}

## controls (N=40, R^2=0.465)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.465
Model:                            OLS   Adj. R-squared:                  0.420
Method:                 Least Squares   F-statistic:                     12.81
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           0.000266
Time:                        02:44:37   Log-Likelihood:                -101.16
No. Observations:                  40   AIC:                             210.3
Df Residuals:                      36   BIC:                             217.1
Df Model:                           3                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               33.1093      8.951      3.699      0.000      15.565      50.653
C(sector)[T.private]    -6.9426      1.910     -3.635      0.000     -10.686      -3.199
C(sector)[T.public]     -1.5483      1.870     -0.828      0.408      -5.213       2.117
log_enrollment          -3.4266      1.277     -2.684      0.007      -5.929      -0.924
==============================================================================
Omnibus:                       19.336   Durbin-Watson:                   0.939
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               31.229
Skew:                           1.311   Prob(JB):                     1.66e-07
Kurtosis:                       6.444   Cond. No.                         93.4
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## star (N=40, R^2=0.619)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.619
Model:                            OLS   Adj. R-squared:                  0.575
Method:                 Least Squares   F-statistic:                     17.30
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           2.61e-05
Time:                        02:44:37   Log-Likelihood:                -94.386
No. Observations:                  40   AIC:                             198.8
Df Residuals:                      35   BIC:                             207.2
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               22.1029      4.911      4.500      0.000      12.477      31.729
C(sector)[T.private]    -3.0766      1.204     -2.555      0.011      -5.437      -0.716
C(sector)[T.public]     -0.7617      1.267     -0.601      0.548      -3.244       1.721
log_enrollment          -1.6323      0.732     -2.229      0.026      -3.068      -0.197
lag_star_z               4.3204      1.008      4.286      0.000       2.344       6.296
==============================================================================
Omnibus:                       19.942   Durbin-Watson:                   2.015
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               34.403
Skew:                           1.311   Prob(JB):                     3.38e-08
Kurtosis:                       6.710   Cond. No.                         105.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## depth (N=40, R^2=0.689)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.689
Model:                            OLS   Adj. R-squared:                  0.653
Method:                 Least Squares   F-statistic:                     26.99
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           1.89e-06
Time:                        02:44:37   Log-Likelihood:                -90.317
No. Observations:                  40   AIC:                             190.6
Df Residuals:                      35   BIC:                             199.1
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               11.5251      5.710      2.018      0.044       0.334      22.717
C(sector)[T.private]    -1.9084      1.778     -1.074      0.283      -5.392       1.575
C(sector)[T.public]     -1.1612      1.312     -0.885      0.376      -3.732       1.410
log_enrollment          -0.6244      0.744     -0.839      0.401      -2.083       0.834
lag_depth_z              3.8554      0.804      4.798      0.000       2.280       5.430
==============================================================================
Omnibus:                       28.646   Durbin-Watson:                   2.079
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               64.819
Skew:                           1.805   Prob(JB):                     8.41e-15
Kurtosis:                       8.085   Cond. No.                         120.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## pack_gap (N=40, R^2=0.527)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.527
Model:                            OLS   Adj. R-squared:                  0.473
Method:                 Least Squares   F-statistic:                     15.33
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           5.14e-05
Time:                        02:44:37   Log-Likelihood:                -98.684
No. Observations:                  40   AIC:                             207.4
Df Residuals:                      35   BIC:                             215.8
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               24.6629      8.450      2.919      0.004       8.101      41.225
C(sector)[T.private]    -5.8050      2.129     -2.726      0.006      -9.979      -1.631
C(sector)[T.public]     -1.7745      1.912     -0.928      0.353      -5.522       1.974
log_enrollment          -2.5642      1.168     -2.194      0.028      -4.854      -0.274
lag_pack_gap             2.7685      0.928      2.982      0.003       0.949       4.588
==============================================================================
Omnibus:                       20.477   Durbin-Watson:                   1.147
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               35.762
Skew:                           1.345   Prob(JB):                     1.72e-08
Kurtosis:                       6.771   Cond. No.                         109.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## star_gap (N=40, R^2=0.698)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.698
Model:                            OLS   Adj. R-squared:                  0.654
Method:                 Least Squares   F-statistic:                     26.42
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           1.16e-06
Time:                        02:44:37   Log-Likelihood:                -89.725
No. Observations:                  40   AIC:                             191.5
Df Residuals:                      34   BIC:                             201.6
Df Model:                           5                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               11.9150      4.818      2.473      0.013       2.473      21.357
C(sector)[T.private]    -1.5682      1.474     -1.064      0.287      -4.456       1.320
C(sector)[T.public]     -0.9726      1.176     -0.827      0.408      -3.278       1.333
log_enrollment          -0.5537      0.620     -0.893      0.372      -1.769       0.662
lag_star_z               4.5673      0.796      5.741      0.000       3.008       6.127
lag_pack_gap             3.1331      0.890      3.522      0.000       1.390       4.877
==============================================================================
Omnibus:                       27.661   Durbin-Watson:                   2.238
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               61.181
Skew:                           1.743   Prob(JB):                     5.19e-14
Kurtosis:                       7.956   Cond. No.                         122.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## both (N=40, R^2=0.698)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.698
Model:                            OLS   Adj. R-squared:                  0.654
Method:                 Least Squares   F-statistic:                     26.42
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           1.16e-06
Time:                        02:44:37   Log-Likelihood:                -89.725
No. Observations:                  40   AIC:                             191.5
Df Residuals:                      34   BIC:                             201.6
Df Model:                           5                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept               11.9150      4.818      2.473      0.013       2.473      21.357
C(sector)[T.private]    -1.5682      1.474     -1.064      0.287      -4.456       1.320
C(sector)[T.public]     -0.9726      1.176     -0.827      0.408      -3.278       1.333
log_enrollment          -0.5537      0.620     -0.893      0.372      -1.769       0.662
lag_star_z               1.4341      1.032      1.390      0.165      -0.589       3.457
lag_depth_z              3.1331      0.890      3.522      0.000       1.390       4.877
==============================================================================
Omnibus:                       27.661   Durbin-Watson:                   2.238
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               61.181
Skew:                           1.743   Prob(JB):                     5.19e-14
Kurtosis:                       7.956   Cond. No.                         121.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## wcac (N=40, R^2=0.699)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_place   R-squared:                       0.699
Model:                            OLS   Adj. R-squared:                  0.644
Method:                 Least Squares   F-statistic:                     136.6
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           1.32e-11
Time:                        02:44:37   Log-Likelihood:                -89.656
No. Observations:                  40   AIC:                             193.3
Df Residuals:                      33   BIC:                             205.1
Df Model:                           6                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept                9.9528      5.918      1.682      0.093      -1.647      21.552
C(sector)[T.private]    -1.2833      1.660     -0.773      0.439      -4.537       1.970
C(sector)[T.public]     -1.1095      1.120     -0.990      0.322      -3.305       1.086
log_enrollment          -0.2585      0.760     -0.340      0.734      -1.747       1.230
lag_star_z               1.4463      1.047      1.382      0.167      -0.605       3.497
lag_depth_z              3.1407      0.905      3.470      0.001       1.367       4.915
wcac                    -0.5221      0.678     -0.770      0.441      -1.850       0.806
==============================================================================
Omnibus:                       27.650   Durbin-Watson:                   2.252
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               61.639
Skew:                           1.736   Prob(JB):                     4.12e-14
Kurtosis:                       7.993   Cond. No.                         158.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## score_controls (N=40, R^2=0.506)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_score   R-squared:                       0.506
Model:                            OLS   Adj. R-squared:                  0.465
Method:                 Least Squares   F-statistic:                     27.71
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           3.80e-06
Time:                        02:44:37   Log-Likelihood:                -227.26
No. Observations:                  40   AIC:                             462.5
Df Residuals:                      36   BIC:                             469.3
Df Model:                           3                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept              806.5016    214.371      3.762      0.000     386.343    1226.660
C(sector)[T.private]  -180.9500     24.472     -7.394      0.000    -228.914    -132.986
C(sector)[T.public]    -54.4265     39.530     -1.377      0.169    -131.904      23.051
log_enrollment         -80.2786     32.039     -2.506      0.012    -143.073     -17.484
==============================================================================
Omnibus:                        1.890   Durbin-Watson:                   1.175
Prob(Omnibus):                  0.389   Jarque-Bera (JB):                0.962
Skew:                          -0.305   Prob(JB):                        0.618
Kurtosis:                       3.452   Cond. No.                         93.4
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## score_star (N=40, R^2=0.633)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_score   R-squared:                       0.633
Model:                            OLS   Adj. R-squared:                  0.591
Method:                 Least Squares   F-statistic:                     50.36
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           3.69e-08
Time:                        02:44:37   Log-Likelihood:                -221.29
No. Observations:                  40   AIC:                             452.6
Df Residuals:                      35   BIC:                             461.0
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept              562.6310    143.792      3.913      0.000     280.804     844.458
C(sector)[T.private]   -95.2896     29.394     -3.242      0.001    -152.901     -37.678
C(sector)[T.public]    -36.9960     38.230     -0.968      0.333    -111.926      37.934
log_enrollment         -40.5218     21.733     -1.865      0.062     -83.117       2.073
lag_star_z              95.7276     29.153      3.284      0.001      38.588     152.867
==============================================================================
Omnibus:                       12.415   Durbin-Watson:                   2.000
Prob(Omnibus):                  0.002   Jarque-Bera (JB):               14.524
Skew:                          -0.971   Prob(JB):                     0.000702
Kurtosis:                       5.223   Cond. No.                         105.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## score_depth (N=40, R^2=0.750)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_score   R-squared:                       0.750
Model:                            OLS   Adj. R-squared:                  0.721
Method:                 Least Squares   F-statistic:                     96.39
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           5.03e-10
Time:                        02:44:37   Log-Likelihood:                -213.63
No. Observations:                  40   AIC:                             437.3
Df Residuals:                      35   BIC:                             445.7
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept              257.9221    171.415      1.505      0.132     -78.044     593.888
C(sector)[T.private]   -53.0019     29.475     -1.798      0.072    -110.771       4.768
C(sector)[T.public]    -44.5874     25.393     -1.756      0.079     -94.357       5.183
log_enrollment          -9.0594     24.245     -0.374      0.709     -56.579      38.461
lag_depth_z             97.9870     19.873      4.931      0.000      59.036     136.938
==============================================================================
Omnibus:                        3.677   Durbin-Watson:                   1.860
Prob(Omnibus):                  0.159   Jarque-Bera (JB):                2.424
Skew:                          -0.501   Prob(JB):                        0.298
Kurtosis:                       3.672   Cond. No.                         120.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## score_pack_gap (N=40, R^2=0.604)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_score   R-squared:                       0.604
Model:                            OLS   Adj. R-squared:                  0.559
Method:                 Least Squares   F-statistic:                     36.74
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           2.78e-07
Time:                        02:44:37   Log-Likelihood:                -222.82
No. Observations:                  40   AIC:                             455.6
Df Residuals:                      35   BIC:                             464.1
Df Model:                           4                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept              548.3037    237.494      2.309      0.021      82.823    1013.784
C(sector)[T.private]  -146.1735     28.315     -5.162      0.000    -201.670     -90.677
C(sector)[T.public]    -61.3384     35.573     -1.724      0.085    -131.059       8.383
log_enrollment         -53.9158     33.157     -1.626      0.104    -118.902      11.071
lag_pack_gap            84.6288     25.507      3.318      0.001      34.637     134.621
==============================================================================
Omnibus:                        0.218   Durbin-Watson:                   1.242
Prob(Omnibus):                  0.897   Jarque-Bera (JB):                0.239
Skew:                          -0.155   Prob(JB):                        0.888
Kurtosis:                       2.784   Cond. No.                         109.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)


## score_both (N=40, R^2=0.751)

                            OLS Regression Results                            
==============================================================================
Dep. Variable:            state_score   R-squared:                       0.751
Model:                            OLS   Adj. R-squared:                  0.714
Method:                 Least Squares   F-statistic:                     97.10
Date:                Sat, 15 Aug 2026   Prob (F-statistic):           2.33e-10
Time:                        02:44:37   Log-Likelihood:                -213.57
No. Observations:                  40   AIC:                             439.1
Df Residuals:                      34   BIC:                             449.3
Df Model:                           5                                         
Covariance Type:              cluster                                         
========================================================================================
                           coef    std err          z      P>|z|      [0.025      0.975]
----------------------------------------------------------------------------------------
Intercept              260.6918    175.576      1.485      0.138     -83.430     604.814
C(sector)[T.private]   -50.5850     27.590     -1.833      0.067    -104.660       3.490
C(sector)[T.public]    -43.2476     29.412     -1.470      0.141    -100.894      14.398
log_enrollment          -8.5573     23.080     -0.371      0.711     -53.793      36.678
lag_star_z              10.1876     36.461      0.279      0.780     -61.275      81.650
lag_depth_z             92.8565     28.883      3.215      0.001      36.248     149.465
==============================================================================
Omnibus:                        4.748   Durbin-Watson:                   1.910
Prob(Omnibus):                  0.093   Jarque-Bera (JB):                3.427
Skew:                          -0.566   Prob(JB):                        0.180
Kurtosis:                       3.881   Cond. No.                         121.
==============================================================================

Notes:
[1] Standard Errors are robust to cluster correlation (cluster)

