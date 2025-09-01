from fpdf import FPDF
import matplotlib.pyplot as plt
import io
import tempfile # Import tempfile
import os       # Import os

class PDFReportGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Relatório de Autonomia de Ração', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}/{{nb}}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(5)

    def chapter_body(self, body):
        self.set_font('Arial', '', 10)
        self.multi_cell(0, 10, body)
        self.ln()

    def add_plot(self, plot_fig):
        # Save the plot to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
            plot_fig.savefig(tmpfile.name, format='png')
            tmp_path = tmpfile.name

        # Add the image to the PDF using the temporary file path
        self.image(tmp_path, x=10, w=self.w - 20) # No need for type='png' if it's a file path

        # Close the plot figure to free memory
        plt.close(plot_fig) # Ensure plot_fig is closed after saving

        # Delete the temporary file
        os.remove(tmp_path)

        self.ln(10)

    def add_aviary_report(self, report_string, plot_fig, aviario_num):
        self.add_page()
        self.chapter_title(f'Aviário {aviario_num}')
        self.chapter_body(report_string)
        self.add_plot(plot_fig)

    def generate_full_report(self, forecaster_instances, output_path):
        self.alias_nb_pages()
        for aviario_num, forecaster_instance in sorted(forecaster_instances.items()):
            self.add_aviary_report(forecaster_instance.report_string, forecaster_instance.plot_fig, aviario_num)
        
        self.output(output_path)