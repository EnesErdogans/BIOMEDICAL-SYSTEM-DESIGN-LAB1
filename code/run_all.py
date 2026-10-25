"""Runs every experiment and rebuilds both reports:  python run_all.py"""
import build_report
import part_a_data
import part_b_linear
import part_c_logistic

if __name__ == "__main__":
    part_a_data.main()
    part_b_linear.main()
    part_c_logistic.main()
    build_report.build("en")
    build_report.build("tr")
