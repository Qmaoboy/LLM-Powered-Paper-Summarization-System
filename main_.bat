@echo off
setlocal enabledelayedexpansion
@REM :init
set currentpath=%cd%/backend/app
set "systemdrive=!currentpath:~0,1!"
set minicondapath=C:\ProgramData\miniconda3
set User_minicondapath=C:\Users\%UserName%\miniconda3
set paddle_env_path1=C:\Users\%UserName%\.conda\envs\paddle_env\Scripts
set paddle_env_path2=C:\Users\%UserName%\miniconda3\envs\paddle_env\Scripts
set envbuild_bat_file=%cd%\Env_build\Env_build.bat

goto Check_env

@REM :change_to_
@REM @REM echo changetoD
@REM %systemdrive%:
@REM goto continue

:patt_switch
call %User_minicondapath%\Scripts\activate.bat 2>nul
call %User_minicondapath%\Scripts\activate paddle_env 2>nul
if errorlevel 1
    echo miniconda env check Fail, Please Check the miniconda env path
    goto END
else
    goto continue

:Check_env
if not exist "%paddle_env_path1%\" (
    if not exist "%paddle_env_path2%\" (
    echo paddle_env env check Fail Start to rebuild paddle_env
    Call %envbuild_bat_file% 2>nul
    goto :START
)
) else (
    echo paddle_env env check Pass activate paddle_env
    goto :START
)

:START
C:
call %minicondapath%\Scripts\activate.bat 2>nul
call %minicondapath%\Scripts\activate paddle_env 2>nul
if errorlevel 1 goto patt_switch
%systemdrive%:
:continue
echo paddle_env activate success
cd %currentpath%
echo %cd%
echo =========== Main Page ===========
echo What Task do u wanna do :
echo 1. GPT_gen
echo 2. Database Function
echo 3. End The PROGRAM
set /p task=
if "%task%" == "1" (
python Main.py GPT_gen
)
if "%task%" == "2" (
python Main.py sql_Action
)
if "%task%" == "3" (
GOTO :END
)
GOTO :continue
:END
echo ===========END Program ===========
endlocal
pause
